# IaC, Environments, Release and Rollback

Follow the plan's ADRs for tool (Terraform default; CDK/CloudFormation if the plan says) and cloud. Existing IaC from the design phase is the starting point: review, fix, complete; do not rewrite from scratch.

## Gap analysis recipe

1. Take the diagram inventory (`diagram-inventory.md`) infrastructure page: list every cloud component.
2. Take the code's needs: queues, topics, buckets, tables, secrets, roles, schedules, endpoints, network paths, KMS keys.
3. Take the existing `terraform/`: list resources and variables.
4. Produce a 3-way table: component -> in diagram? -> in IaC? -> used by code? Mark missing, orphaned, mismatched (names, regions, retention, encryption).
5. Check guardrails: IAM policies contain no forbidden actions (list them from the plan); write-once or read-only where the plan says; no public access; encryption at rest and in transit; logging enabled.

## Terraform layout

```text
terraform/
  modules/<container>/        # one module per diagram container; inputs documented; outputs minimal
  envs/{dev,staging,prod,dr}/ # main.tf, variables.tf, terraform.tfvars.example, backend.tf
  versions.tf                 # required_version and provider constraints; commit .terraform.lock.hcl
```

Rules: remote state (bucket/table or equivalent) with locking and encryption, created by a separate bootstrap that is documented not auto-run; variables for account, region, naming prefix, tags; `sensitive = true` outputs; no secrets in `tfvars` committed (`*.tfvars.example` only); `prevent_destroy` on stateful resources (data, evidence, keys); lifecycle and retention from the plan; tags `project, env, owner, data_class, cost_center`.

## Validation commands and how to record them

| Check | Command | Needs credentials |
| :-- | :-- | :-: |
| Format | `terraform fmt -check -recursive` | No |
| Init without backend | `terraform init -backend=false` | No |
| Validate | `terraform validate` | No |
| Lint | `tflint --recursive` | No |
| Security scan | `checkov -d terraform` or `trivy config terraform` | No |
| Policy checks | `conftest` / OPA rules for guardrails (for example deny `*` actions, deny payment services) | No |
| Plan | `terraform plan -out=plan.tfplan` | Yes (non-production only, user-provided) |
| Cost estimate | `infracost breakdown` | Optional |

Record each as RAN with result, or NOT RUN with the reason. Never `terraform apply` or `destroy`.

## Environments

| Env | Purpose | Data | Differences |
| :-- | :-- | :-- | :-- |
| local | developer/tester compose | synthetic | emulators, fake model |
| dev | integration of merged work | synthetic | smallest sizes, shared account OK |
| staging | prod-like, shadow-mode | masked/real per plan approval | same topology as prod, smaller scale |
| prod | live | real | HA, backups, alarms, restricted access |
| dr | per plan RTO/RPO | replicated | warm/cold per plan |

Configuration is environment variables + parameter store; the same artifact moves through environments (build once, promote). No environment-specific code branches.

## Release strategy

- Immutable artifacts tagged by commit SHA; release notes generated from merged PRs and the requirement IDs touched.
- Database migrations: expand -> migrate -> contract; each deployable with both old and new code; migrations tested forward on a populated database; destructive steps in a later release.
- Feature flags / kill-switches from the plan (for example `review_only_mode`) stored in config, changeable without deploy, audited.
- Rollout per plan: shadow -> review-only -> partial automation -> full; canary percentage or tenant-based; explicit success metrics and hold points.
- Rollback: previous artifact redeploy by SHA; data compatibility stated; model/prompt/policy pointer revert; for irreversible steps, a documented compensation.
- Smoke tests after each deploy hit health, one read path, one safe write path with synthetic data tagged `FAKE`, and verify metrics and logs appear.
- Rollback rehearsal in staging: record as REHEARSED (date, evidence) or NOT REHEARSED.

## Secrets and identity

- Secret manager for runtime secrets; references by name/ARN in config; rotation policy stated.
- CI to cloud via OIDC trust policy scoped to repo + environment; separate roles for plan (read) and apply (write).
- Workload roles per component, least privilege, mapped to the component table; break-glass role documented and alarmed.
- No static access keys anywhere; scan to prove it.

## Drift and cost

- Scheduled `terraform plan` (drift detection) in a non-prod/read-only role, alert on diff.
- Budgets and anomaly alerts per environment; tag-based cost reports; model spend metric from the application; CI minute usage noted in the hand-off.
