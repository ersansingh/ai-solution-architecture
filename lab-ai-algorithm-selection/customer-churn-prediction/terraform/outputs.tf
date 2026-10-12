# =========================================================================
# CUSTOMER CHURN PREDICTION PLATFORM - OUTPUTS
# =========================================================================

output "resource_group_name" {
  description = "Resource group hosting the churn platform."
  value       = azurerm_resource_group.main.name
}

output "hub_vnet_id" {
  description = "Hub VNet ID (Firewall, Bastion, gateway)."
  value       = azurerm_virtual_network.hub.id
}

output "spoke_vnet_id" {
  description = "Spoke VNet ID (workloads)."
  value       = azurerm_virtual_network.spoke.id
}

output "spoke_subnet_ids" {
  description = "Spoke subnet IDs keyed by name."
  value       = { for k, s in azurerm_subnet.spoke : k => s.id }
}

output "firewall_private_ip" {
  description = "Azure Firewall private IP (next hop for spoke egress)."
  value       = azurerm_firewall.hub.ip_configuration[0].private_ip_address
}

output "aks_cluster_name" {
  description = "AKS private cluster name (KServe serving)."
  value       = azurerm_kubernetes_cluster.main.name
}

output "aks_oidc_issuer_url" {
  description = "AKS OIDC issuer used for workload identity federation."
  value       = azurerm_kubernetes_cluster.main.oidc_issuer_url
}

output "serving_workload_identity_client_id" {
  description = "Client ID to annotate on the KServe service account (azure.workload.identity/client-id)."
  value       = azurerm_user_assigned_identity.serving.client_id
}

output "acr_login_server" {
  description = "Container registry login server for model-server images."
  value       = azurerm_container_registry.main.login_server
}

output "aml_workspace_name" {
  description = "Azure ML workspace (MLflow tracking + model registry)."
  value       = azurerm_machine_learning_workspace.main.name
}

output "aml_compute_clusters" {
  description = "Azure ML CPU compute clusters."
  value = {
    training = azurerm_machine_learning_compute_cluster.training.name
    tuning   = azurerm_machine_learning_compute_cluster.tuning.name
    batch    = azurerm_machine_learning_compute_cluster.batch.name
  }
}

output "databricks_workspace_url" {
  description = "Databricks workspace URL (resolves privately)."
  value       = azurerm_databricks_workspace.main.workspace_url
}

output "lake_storage_account_name" {
  description = "ADLS Gen2 account for the Delta medallion lake and Feast offline store."
  value       = azurerm_storage_account.lake.name
}

output "lake_dfs_endpoint" {
  description = "ADLS Gen2 DFS endpoint."
  value       = azurerm_storage_account.lake.primary_dfs_endpoint
}

output "eventhub_namespace_fqdn" {
  description = "Event Hubs namespace FQDN for streaming features."
  value       = "${azurerm_eventhub_namespace.main.name}.servicebus.windows.net"
}

output "redis_hostname" {
  description = "Feast online store (Azure Cache for Redis Premium) host name."
  value       = azurerm_redis_cache.feast_online.hostname
}

output "redis_ssl_port" {
  description = "Redis TLS port."
  value       = azurerm_redis_cache.feast_online.ssl_port
}

output "key_vault_uri" {
  description = "Key Vault URI."
  value       = azurerm_key_vault.main.vault_uri
}

output "cmk_key_id" {
  description = "Versionless customer-managed key ID."
  value       = azurerm_key_vault_key.cmk.versionless_id
}

output "apim_gateway_private_ips" {
  description = "APIM internal gateway private IPs."
  value       = azurerm_api_management.main.private_ip_addresses
}

output "appgw_private_frontend_ips" {
  description = "Application Gateway private frontend IPs (Front Door Private Link origins) keyed by region."
  value       = { for k, v in local.api_ingress_regions : k => v.private_ip }
}

output "appgw_names" {
  description = "Application Gateways whose pending Front Door private endpoint connections must be approved after the first apply."
  value       = { for k, agw in azurerm_application_gateway.api : k => agw.name }
}

output "frontdoor_endpoint_hostname" {
  description = "Public Front Door endpoint for the churn scoring API."
  value       = azurerm_cdn_frontdoor_endpoint.api.host_name
}

output "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID."
  value       = azurerm_log_analytics_workspace.main.id
}

output "application_insights_connection_string" {
  description = "App Insights connection string for OpenTelemetry exporters."
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "grafana_endpoint" {
  description = "Azure Managed Grafana endpoint."
  value       = azurerm_dashboard_grafana.main.endpoint
}

output "dr_resource_group_name" {
  description = "North Europe DR (warm standby) resource group."
  value       = azurerm_resource_group.dr.name
}

output "dr_spoke_vnet_id" {
  description = "North Europe DR spoke VNet ID."
  value       = azurerm_virtual_network.dr.id
}

output "dr_aks_cluster_name" {
  description = "Warm-standby AKS cluster in the DR region (null when enable_dr = false)."
  value       = try(azurerm_kubernetes_cluster.dr[0].name, null)
}

output "dr_redis_hostname" {
  description = "Redis geo-replica host name in the DR region (null when enable_dr = false)."
  value       = try(azurerm_redis_cache.feast_online_dr[0].hostname, null)
}

output "purview_account_name" {
  description = "Microsoft Purview account (catalog, classification, lineage)."
  value       = azurerm_purview_account.main.name
}

output "stream_analytics_job_name" {
  description = "Stream Analytics job computing windowed streaming features."
  value       = azurerm_stream_analytics_job.features.name
}

output "redis_aof_persistence_enabled" {
  description = "Whether AOF persistence is active on the primary Redis (only when enable_dr = false; persistence is unsupported on geo-replicated caches)."
  value       = local.redis_aof_enabled
}

output "dr_private_endpoint_ids" {
  description = "DR-region private endpoints (North Europe VNet) keyed by target, empty when enable_dr = false."
  value       = { for k, pe in azurerm_private_endpoint.dr : k => pe.id }
}

output "dr_prometheus_workspace_id" {
  description = "North Europe Azure Monitor workspace receiving the DR AKS managed Prometheus metrics (null when enable_dr = false)."
  value       = try(azurerm_monitor_workspace.prometheus_dr[0].id, null)
}

# Consumed by scripts/post-apply.sh (terraform output -json post_apply_targets)
output "post_apply_targets" {
  description = "Resource IDs and names used by scripts/post-apply.sh and the Purview steps in POST_APPLY.md."
  value = {
    subscription_id                   = data.azurerm_client_config.current.subscription_id
    resource_group_name               = azurerm_resource_group.main.name
    application_gateway_ids           = { for k, agw in azurerm_application_gateway.api : k => agw.id }
    frontdoor_request_message_prefix  = "Front Door private origin for churn scoring API"
    stream_analytics_cluster_enabled  = var.enable_stream_analytics_cluster
    stream_analytics_job_name         = azurerm_stream_analytics_job.features.name
    stream_analytics_private_link_ids = distinct([for v in values(local.asa_private_endpoints) : v.target])
    purview_account_name              = azurerm_purview_account.main.name
    lake_storage_account_id           = azurerm_storage_account.lake.id
    lake_dfs_endpoint                 = azurerm_storage_account.lake.primary_dfs_endpoint
    aml_workspace_id                  = azurerm_machine_learning_workspace.main.id
    location                          = azurerm_resource_group.main.location
  }
}
