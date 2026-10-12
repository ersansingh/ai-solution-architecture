# Post-apply steps

Terraform cannot do these steps itself. Run them after the first `terraform apply`, and again whenever `enable_dr` or `enable_stream_analytics_cluster` changes.

## 1. Before apply: Application Gateway certificate

Front Door Premium connects to the Application Gateway over Private Link. It only trusts an origin certificate signed by a public CA, so self-signed certificates and internal-PKI certificates are rejected.

1. Get a publicly trusted certificate for `api_origin_host_name` (default `api-internal.churn.example.com`) and export it as a PFX.
2. Import it into the platform Key Vault:
   ```bash
   az keyvault certificate import --vault-name <kv> --name appgw-api-origin --file api-origin.pfx
   ```
3. Set `appgw_ssl_certificate_secret_id` to the **versionless** secret ID (`https://<kv>.vault.azure.net/secrets/appgw-api-origin`). The App Gateway then picks up renewals automatically.

`appgw_ssl_certificate_secret_id` has no default, so `terraform plan` fails until it is set.

## 2. Approve private endpoint connections

```bash
terraform/scripts/post-apply.sh --dry-run   # list pending connections
terraform/scripts/post-apply.sh             # approve them
```

The script reads the `post_apply_targets` output and approves:

- **Front Door -> Application Gateway Private Link**: one connection per region (West Europe, plus North Europe when `enable_dr = true`). It only approves requests whose message starts with `frontdoor_request_message_prefix`. Any other pending request is left for manual review.
- **Stream Analytics cluster managed private endpoints -> Event Hubs and the lake** (only when `enable_stream_analytics_cluster = true`). After they show `Approved`, start the ASA job with the command the script prints.

Exit code `3` means something still needs attention. The usual cause is a Front Door origin that has not raised its connection yet: wait a few minutes and run the script again.

## 3. Microsoft Purview: sources, scans and roles

`governance.tf` creates only the account and its private endpoints. Everything below happens in the Purview data plane, which azurerm does not manage. The account name is in `terraform output -json post_apply_targets | jq -r .purview_account_name`.

1. **Integration runtime.** Every source is private-only, so the default Azure IR cannot reach it. Create a managed-VNet IR in West Europe, then add managed private endpoints from it to the lake (`dfs` and `blob`) and the Key Vault. Approve those endpoints on the targets.
2. **Collections and roles.** Create a `churn` collection. Grant the data stewards Data Curator, the auditors Data Reader, and the platform team Data Source Administrator.
3. **Register the sources** under `churn`:
   - ADLS Gen2: the lake account (`lake_storage_account_id`). The Purview managed identity already has Storage Blob Data Reader.
   - Azure Databricks: the workspace in `main.tf`, through Unity Catalog lineage.
   - Azure ML: the workspace (`aml_workspace_id`).
4. **Scans.** Use the managed-VNet IR with the system classification rule set (add custom rules, for example for `pseudo_customer_id`, if the data stewards ask for them). Schedule them weekly, after the Sunday retrain. Scope them to the `silver`, `gold` and `feast-offline` containers. `bronze` holds raw PII and is classified by Presidio upstream, so leave it out.
5. **Check:** you should see lineage from Gold to the Azure ML training job, and PII classifications on Silver columns.

## 4. Decision: `enable_stream_analytics_cluster`

The default is `false`. The Event Hubs namespace and the lake are private-only, so a Standard ASA job cannot reach them, and Databricks Structured Streaming computes the windowed features instead (`system-design.md` 6.3).

Setting it to `true` deploys a dedicated cluster at its minimum size (`streaming_capacity = 36`), which bills around the clock whether or not the job runs. This cost is **not** in the FinOps table (`system-design.md` 12.5). Before enabling it, price 36 SU × 730 h at the current West Europe dedicated-cluster rate, and add that as its own line.
