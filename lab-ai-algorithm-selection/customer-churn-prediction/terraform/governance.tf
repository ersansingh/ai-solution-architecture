# =========================================================================
# CUSTOMER CHURN PREDICTION PLATFORM - DATA GOVERNANCE (MICROSOFT PURVIEW)
# Catalog, PII classification and end-to-end lineage (ADLS, Databricks,
# Azure ML) for GDPR audit. Private-only: `account` and `portal` private
# endpoints are declared in local.private_endpoints (main.tf, section 12).
#
# Follow-up (Purview data plane, not azurerm): register the lake / Databricks /
# AML sources, create scans with a managed-VNet or self-hosted integration
# runtime (sources are private), and assign Purview collection roles.
# =========================================================================
resource "azurerm_purview_account" "main" {
  name                        = "pview-${local.name_prefix}-${random_string.suffix.result}"
  location                    = azurerm_resource_group.main.location
  resource_group_name         = azurerm_resource_group.main.name
  public_network_enabled      = false
  managed_event_hub_enabled   = false # no Kafka notifications needed; avoids a public managed namespace
  managed_resource_group_name = "rg-${local.name_prefix}-purview-managed"

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

# Scanner identity: read-only data access for classification and lineage
resource "azurerm_role_assignment" "purview_lake_reader" {
  scope                = azurerm_storage_account.lake.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_purview_account.main.identity[0].principal_id
}

resource "azurerm_role_assignment" "purview_rg_reader" {
  scope                = azurerm_resource_group.main.id
  role_definition_name = "Reader"
  principal_id         = azurerm_purview_account.main.identity[0].principal_id
}
