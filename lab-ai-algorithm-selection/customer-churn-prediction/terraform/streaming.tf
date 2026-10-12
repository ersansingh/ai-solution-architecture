# =========================================================================
# CUSTOMER CHURN PREDICTION PLATFORM - AZURE STREAM ANALYTICS
# Windowed streaming features (tickets_24h, failed_payments_7d,
# app_sessions_7d) from Event Hubs -> ADLS (silver/streaming-features,
# Parquet), picked up by the Feast push/materialization job. Databricks
# Structured Streaming covers the heavier features (see system-design.md).
#
# Event Hubs and ADLS are public-network-disabled, so the job can only run on
# a dedicated ASA cluster with managed private endpoints
# (var.enable_stream_analytics_cluster). Without it the job is provisioned
# (stopped) but cannot start.
#
# MANUAL STEP: approve the managed private endpoint connections on the Event
# Hubs namespace and the lake storage account after the first apply
# (Portal: <resource> > Networking > Private endpoint connections).
# The job is started by the platform runbook / pipeline
# (az stream-analytics job start), not by Terraform.
# =========================================================================

locals {
  # Inputs share names with the source Event Hubs; the query below refers to them.
  asa_input_hubs = [for k in keys(var.event_hubs) : k if k != "churn-score-feed"]

  asa_private_endpoints = {
    for k, v in {
      eventhub  = { target = azurerm_eventhub_namespace.main.id, subresource = "namespace" }
      lake-blob = { target = azurerm_storage_account.lake.id, subresource = "blob" }
      lake-dfs  = { target = azurerm_storage_account.lake.id, subresource = "dfs" }
    } : k => v if var.enable_stream_analytics_cluster
  }
}

resource "azurerm_stream_analytics_cluster" "main" {
  count               = var.enable_stream_analytics_cluster ? 1 : 0
  name                = "asac-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  streaming_capacity  = 36
  tags                = local.tags
}

resource "azurerm_stream_analytics_managed_private_endpoint" "this" {
  for_each                      = local.asa_private_endpoints
  name                          = "mpe-${each.key}"
  resource_group_name           = azurerm_resource_group.main.name
  stream_analytics_cluster_name = azurerm_stream_analytics_cluster.main[0].name
  target_resource_id            = each.value.target
  subresource_name              = each.value.subresource
}

resource "azurerm_eventhub_consumer_group" "stream_analytics" {
  for_each            = toset(local.asa_input_hubs)
  name                = "asa-windowed-features"
  namespace_name      = azurerm_eventhub_namespace.main.name
  eventhub_name       = azurerm_eventhub.this[each.value].name
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_stream_analytics_job" "features" {
  name                                     = "asa-${local.name_prefix}-features"
  location                                 = azurerm_resource_group.main.location
  resource_group_name                      = azurerm_resource_group.main.name
  sku_name                                 = "Standard"
  streaming_units                          = var.stream_analytics_streaming_units
  stream_analytics_cluster_id              = var.enable_stream_analytics_cluster ? azurerm_stream_analytics_cluster.main[0].id : null
  compatibility_level                      = "1.2"
  data_locale                              = "en-GB"
  events_late_arrival_max_delay_in_seconds = 60
  events_out_of_order_max_delay_in_seconds = 10
  events_out_of_order_policy               = "Adjust"
  output_error_policy                      = "Stop"

  identity {
    type = "SystemAssigned"
  }

  # Long format (customer_id, feature_name, feature_value, event_timestamp).
  # app_sessions_7d_delta is derived downstream from successive app_sessions_7d values.
  transformation_query = <<-QUERY
    SELECT
        customer_id,
        'tickets_24h' AS feature_name,
        CAST(COUNT(*) AS float) AS feature_value,
        System.Timestamp() AS event_timestamp
    INTO [streaming-features]
    FROM [support-calls] TIMESTAMP BY event_time
    GROUP BY customer_id, HoppingWindow(minute, 1440, 5)

    SELECT
        customer_id,
        'failed_payments_7d' AS feature_name,
        CAST(SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS float) AS feature_value,
        System.Timestamp() AS event_timestamp
    INTO [streaming-features]
    FROM [payments] TIMESTAMP BY event_time
    GROUP BY customer_id, HoppingWindow(minute, 10080, 60)

    SELECT
        customer_id,
        'app_sessions_7d' AS feature_name,
        CAST(COUNT(*) AS float) AS feature_value,
        System.Timestamp() AS event_timestamp
    INTO [streaming-features]
    FROM [app-sessions] TIMESTAMP BY event_time
    GROUP BY customer_id, HoppingWindow(minute, 10080, 60)
  QUERY

  tags = local.tags
}

resource "azurerm_stream_analytics_stream_input_eventhub_v2" "this" {
  for_each                     = toset(local.asa_input_hubs)
  name                         = each.value
  stream_analytics_job_id      = azurerm_stream_analytics_job.features.id
  servicebus_namespace         = azurerm_eventhub_namespace.main.name
  eventhub_name                = azurerm_eventhub.this[each.value].name
  eventhub_consumer_group_name = azurerm_eventhub_consumer_group.stream_analytics[each.value].name
  authentication_mode          = "Msi"

  serialization {
    type     = "Json"
    encoding = "UTF8"
  }

  depends_on = [azurerm_role_assignment.asa_eventhub_receiver]
}

resource "azurerm_stream_analytics_output_blob" "features" {
  name                      = "streaming-features"
  stream_analytics_job_name = azurerm_stream_analytics_job.features.name
  resource_group_name       = azurerm_resource_group.main.name
  storage_account_name      = azurerm_storage_account.lake.name
  storage_container_name    = var.stream_analytics_output_container
  path_pattern              = "streaming-features/{date}/{time}"
  date_format               = "yyyy/MM/dd"
  time_format               = "HH"
  authentication_mode       = "Msi"
  batch_min_rows            = 10000
  batch_max_wait_time       = "00:01:00"

  serialization {
    type = "Parquet"
  }

  depends_on = [
    azurerm_role_assignment.asa_lake_contributor,
    azurerm_storage_data_lake_gen2_filesystem.lake,
  ]
}

resource "azurerm_role_assignment" "asa_eventhub_receiver" {
  scope                = azurerm_eventhub_namespace.main.id
  role_definition_name = "Azure Event Hubs Data Receiver"
  principal_id         = azurerm_stream_analytics_job.features.identity[0].principal_id
}

resource "azurerm_role_assignment" "asa_lake_contributor" {
  scope                = azurerm_storage_account.lake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_stream_analytics_job.features.identity[0].principal_id
}
