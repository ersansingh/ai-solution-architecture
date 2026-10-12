# =========================================================================
# CUSTOMER CHURN PREDICTION PLATFORM - NORTH EUROPE DR (WARM STANDBY)
# Active-passive: Front Door priority failover to a minimum-scale serving
# stack (AKS + Redis geo-replica + APIM regional unit + App Gateway).
# Lake (GZRS) and ACR (geo-replication) are replicated from main.tf.
# Batch/training (ADF, Databricks, AML) are redeployed from IaC on failover.
#
# Always deployed (cheap): DR resource group, spoke VNet 10.30.0.0/16,
# subnets, NSGs, DR-region privatelink DNS zones and links, global peering to
# the primary spoke.
# Gated by var.enable_dr (costly): DR AKS (+ managed Prometheus), Redis
# geo-replica, DR-region private endpoints (Key Vault, ACR, lake, AML, Event
# Hubs), APIM additional_location (main.tf), DR App Gateway + Front Door
# origin (main.tf).
#
# Egress: the DR cluster always uses userDefinedRouting through the
# platform-owned North Europe hub firewall. enable_dr = true therefore requires
# dr_hub_vnet_id and dr_hub_firewall_private_ip (precondition on the cluster);
# there is no load-balancer public-IP fallback ("deny public IPs" policy).
# =========================================================================

locals {
  dr_name_prefix = "${local.name_prefix}-dr"

  dr_tags = merge(local.tags, {
    DRRole = "WarmStandby"
  })

  # Same NSG baseline as the primary spoke; AKS ingress allowed from the DR APIM subnet
  dr_nsg_rules = merge(local.nsg_rules, {
    snet-aks-user = [
      { name = "Allow-APIM-To-Ingress", priority = 100, direction = "Inbound", protocol = "Tcp", source = var.dr_spoke_subnets["snet-apim"].cidr, destination = "VirtualNetwork", port = "443" },
    ]
  })

  dr_udr_enabled = var.dr_hub_firewall_private_ip != null

  # Per-region private DNS: services that get a DR-region private endpoint have
  # their own privatelink zones (DR resource group) linked ONLY to the DR VNet,
  # so DR workloads resolve to DR endpoints and primary workloads keep resolving
  # to primary endpoints (same FQDN, different A records per region). The
  # remaining zones (no DR endpoint: Databricks, ADF, Purview) stay shared with
  # the primary and are linked to the DR VNet for reachability over peering.
  dr_private_dns_zone_keys = ["blob", "dfs", "vault", "acr", "redis", "eventhub", "aml_api", "aml_nb"]
  dr_private_dns_zones     = { for k in local.dr_private_dns_zone_keys : k => local.private_dns_zones[k] }
  dr_shared_dns_zones      = { for k, v in local.private_dns_zones : k => v if !contains(local.dr_private_dns_zone_keys, k) }

  # DR-region private endpoints to the (single-region) primary services. Key
  # Vault, the lake account and the AML workspace stay West Europe resources
  # (GZRS / Microsoft-managed KV failover); the endpoints remove the DR data
  # path's dependency on the primary spoke's endpoints and global peering.
  dr_private_endpoints = var.enable_dr ? {
    lake-blob     = { resource_id = azurerm_storage_account.lake.id, subresource = "blob", zones = ["blob"] }
    lake-dfs      = { resource_id = azurerm_storage_account.lake.id, subresource = "dfs", zones = ["dfs"] }
    aml-blob      = { resource_id = azurerm_storage_account.aml.id, subresource = "blob", zones = ["blob"] }
    keyvault      = { resource_id = azurerm_key_vault.main.id, subresource = "vault", zones = ["vault"] }
    acr           = { resource_id = azurerm_container_registry.main.id, subresource = "registry", zones = ["acr"] }
    eventhub      = { resource_id = azurerm_eventhub_namespace.main.id, subresource = "namespace", zones = ["eventhub"] }
    aml-workspace = { resource_id = azurerm_machine_learning_workspace.main.id, subresource = "amlworkspace", zones = ["aml_api", "aml_nb"] }
  } : {}
}

# =========================================================================
# DR.1 RESOURCE GROUP + SPOKE VNET
# =========================================================================
resource "azurerm_resource_group" "dr" {
  name     = "rg-${local.name_prefix}-${var.dr_location}"
  location = var.dr_location
  tags     = local.dr_tags
}

resource "azurerm_virtual_network" "dr" {
  name                = "vnet-spoke-${local.dr_name_prefix}"
  location            = azurerm_resource_group.dr.location
  resource_group_name = azurerm_resource_group.dr.name
  address_space       = [var.dr_spoke_vnet_cidr]
  tags                = local.dr_tags
}

resource "azurerm_subnet" "dr" {
  for_each             = var.dr_spoke_subnets
  name                 = each.key
  resource_group_name  = azurerm_resource_group.dr.name
  virtual_network_name = azurerm_virtual_network.dr.name
  address_prefixes     = [each.value.cidr]

  private_endpoint_network_policies             = each.key == "snet-private-endpoints" ? "Enabled" : "Disabled"
  private_link_service_network_policies_enabled = each.key != "snet-appgw-pl"

  dynamic "delegation" {
    for_each = each.value.delegation == null ? [] : [each.value.delegation]
    content {
      name = "delegation-${replace(delegation.value, "/", "-")}"
      service_delegation {
        name = delegation.value
        actions = [
          "Microsoft.Network/virtualNetworks/subnets/join/action",
          "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action",
          "Microsoft.Network/virtualNetworks/subnets/unprepareNetworkPolicies/action",
        ]
      }
    }
  }
}

resource "azurerm_network_security_group" "dr" {
  for_each            = var.dr_spoke_subnets
  name                = "nsg-${each.key}-${local.dr_name_prefix}"
  location            = azurerm_resource_group.dr.location
  resource_group_name = azurerm_resource_group.dr.name

  dynamic "security_rule" {
    for_each = lookup(local.dr_nsg_rules, each.key, [])
    content {
      name                       = security_rule.value.name
      priority                   = security_rule.value.priority
      direction                  = security_rule.value.direction
      access                     = startswith(security_rule.value.name, "Deny") ? "Deny" : "Allow"
      protocol                   = security_rule.value.protocol
      source_port_range          = "*"
      destination_port_range     = security_rule.value.port
      source_address_prefix      = security_rule.value.source
      destination_address_prefix = security_rule.value.destination
    }
  }

  tags = local.dr_tags
}

resource "azurerm_subnet_network_security_group_association" "dr" {
  for_each                  = var.dr_spoke_subnets
  subnet_id                 = azurerm_subnet.dr[each.key].id
  network_security_group_id = azurerm_network_security_group.dr[each.key].id
}

# -------------------------------------------------------------------------
# DR.2 Peering: global VNet peering to the primary spoke (replication and the
# shared Databricks/ADF/Purview endpoints), NEU hub peering (required for DR
# egress when enable_dr = true).
# -------------------------------------------------------------------------
resource "azurerm_virtual_network_peering" "dr_to_spoke" {
  name                         = "peer-dr-to-spoke"
  resource_group_name          = azurerm_resource_group.dr.name
  virtual_network_name         = azurerm_virtual_network.dr.name
  remote_virtual_network_id    = azurerm_virtual_network.spoke.id
  allow_forwarded_traffic      = true
  allow_virtual_network_access = true
}

resource "azurerm_virtual_network_peering" "spoke_to_dr" {
  name                         = "peer-spoke-to-dr"
  resource_group_name          = azurerm_resource_group.main.name
  virtual_network_name         = azurerm_virtual_network.spoke.name
  remote_virtual_network_id    = azurerm_virtual_network.dr.id
  allow_forwarded_traffic      = true
  allow_virtual_network_access = true
}

# The hub -> DR spoke side is created by the platform team in the NEU hub.
resource "azurerm_virtual_network_peering" "dr_to_dr_hub" {
  count                        = var.dr_hub_vnet_id == null ? 0 : 1
  name                         = "peer-dr-to-neu-hub"
  resource_group_name          = azurerm_resource_group.dr.name
  virtual_network_name         = azurerm_virtual_network.dr.name
  remote_virtual_network_id    = var.dr_hub_vnet_id
  allow_forwarded_traffic      = true
  allow_virtual_network_access = true
}

# Forced tunnelling of DR AKS egress through the NEU hub firewall (if provided)
resource "azurerm_route_table" "dr_egress" {
  count               = local.dr_udr_enabled ? 1 : 0
  name                = "rt-spoke-egress-${local.dr_name_prefix}"
  location            = azurerm_resource_group.dr.location
  resource_group_name = azurerm_resource_group.dr.name

  route {
    name                   = "default-via-neu-firewall"
    address_prefix         = "0.0.0.0/0"
    next_hop_type          = "VirtualAppliance"
    next_hop_in_ip_address = var.dr_hub_firewall_private_ip
  }

  tags = local.dr_tags
}

resource "azurerm_subnet_route_table_association" "dr" {
  for_each       = { for k, v in var.dr_spoke_subnets : k => v if v.udr && local.dr_udr_enabled }
  subnet_id      = azurerm_subnet.dr[each.key].id
  route_table_id = azurerm_route_table.dr_egress[0].id
}

# -------------------------------------------------------------------------
# DR.3 Private DNS (per-region zones) + DR-region private endpoints.
# A VNet can link only one zone per name, so the DR VNet links the DR copy of
# each regional zone and the primary copy of the shared ones. The DR zones and
# links are always deployed (cheap, and toggling enable_dr never has to swap a
# link between two same-named zones); the endpoints are gated by enable_dr.
#
# ACR: the registry endpoint in the DR VNet publishes the login server and the
# regional data endpoints (<acr>.northeurope.data / .westeurope.data) into the
# DR acr zone with DR-subnet IPs, so DR nodes pull from the North Europe
# geo-replica without crossing regions.
# -------------------------------------------------------------------------
resource "azurerm_private_dns_zone" "dr" {
  for_each            = local.dr_private_dns_zones
  name                = each.value
  resource_group_name = azurerm_resource_group.dr.name
  tags                = local.dr_tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "dr_regional" {
  for_each              = local.dr_private_dns_zones
  name                  = "link-${each.key}-dr"
  resource_group_name   = azurerm_resource_group.dr.name
  private_dns_zone_name = azurerm_private_dns_zone.dr[each.key].name
  virtual_network_id    = azurerm_virtual_network.dr.id
  registration_enabled  = false
  tags                  = local.dr_tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "dr" {
  for_each              = local.dr_shared_dns_zones
  name                  = "link-${each.key}-dr"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.this[each.key].name
  virtual_network_id    = azurerm_virtual_network.dr.id
  registration_enabled  = false
  tags                  = local.dr_tags
}

resource "azurerm_private_endpoint" "dr" {
  for_each            = local.dr_private_endpoints
  name                = "pe-${each.key}-${local.dr_name_prefix}"
  location            = azurerm_resource_group.dr.location
  resource_group_name = azurerm_resource_group.dr.name
  subnet_id           = azurerm_subnet.dr["snet-private-endpoints"].id

  private_service_connection {
    name                           = "psc-${each.key}-dr"
    private_connection_resource_id = each.value.resource_id
    subresource_names              = [each.value.subresource]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-${each.key}-dr"
    private_dns_zone_ids = [for z in each.value.zones : azurerm_private_dns_zone.dr[z].id]
  }

  tags = local.dr_tags
}

# =========================================================================
# DR.4 WARM STANDBY AKS (MINIMUM SCALE, SAME ARGO CD APPS)
# =========================================================================
resource "azurerm_user_assigned_identity" "aks_dr" {
  count               = var.enable_dr ? 1 : 0
  name                = "id-aks-${local.dr_name_prefix}"
  location            = azurerm_resource_group.dr.location
  resource_group_name = azurerm_resource_group.dr.name
  tags                = local.dr_tags
}

resource "azurerm_role_assignment" "aks_dr_network_contributor" {
  count                = var.enable_dr ? 1 : 0
  scope                = azurerm_virtual_network.dr.id
  role_definition_name = "Network Contributor"
  principal_id         = azurerm_user_assigned_identity.aks_dr[0].principal_id
}

resource "azurerm_role_assignment" "aks_dr_route_table" {
  count                = var.enable_dr && local.dr_udr_enabled ? 1 : 0
  scope                = azurerm_route_table.dr_egress[0].id
  role_definition_name = "Network Contributor"
  principal_id         = azurerm_user_assigned_identity.aks_dr[0].principal_id
}

resource "azurerm_kubernetes_cluster" "dr" {
  count                     = var.enable_dr ? 1 : 0
  name                      = "aks-${local.dr_name_prefix}"
  location                  = azurerm_resource_group.dr.location
  resource_group_name       = azurerm_resource_group.dr.name
  dns_prefix                = "aks-${local.dr_name_prefix}"
  kubernetes_version        = var.kubernetes_version
  sku_tier                  = "Standard"
  private_cluster_enabled   = true
  private_dns_zone_id       = "System"
  local_account_disabled    = true
  oidc_issuer_enabled       = true
  workload_identity_enabled = true
  azure_policy_enabled      = true
  automatic_upgrade_channel = "patch"
  node_os_upgrade_channel   = "NodeImage"

  default_node_pool {
    name                         = "system"
    vm_size                      = var.aks_system_vm_size
    zones                        = var.availability_zones
    vnet_subnet_id               = azurerm_subnet.dr["snet-aks-system"].id
    auto_scaling_enabled         = true
    min_count                    = var.aks_system_node_count.min
    max_count                    = var.aks_system_node_count.max
    only_critical_addons_enabled = true
    os_disk_type                 = "Ephemeral"
    os_disk_size_gb              = 128
    max_pods                     = 110
    temporary_name_for_rotation  = "systemtmp"

    upgrade_settings {
      max_surge = "33%"
    }

    tags = local.dr_tags
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aks_dr[0].id]
  }

  # Forced tunnelling through the NEU hub firewall, like the primary. No
  # load-balancer outbound public IP (see the precondition below).
  network_profile {
    network_plugin      = "azure"
    network_plugin_mode = "overlay"
    network_data_plane  = "cilium"
    network_policy      = "cilium"
    outbound_type       = "userDefinedRouting"
    load_balancer_sku   = "standard"
    pod_cidr            = var.aks_pod_cidr
    service_cidr        = var.aks_service_cidr
    dns_service_ip      = var.aks_dns_service_ip
  }

  azure_active_directory_role_based_access_control {
    tenant_id              = data.azurerm_client_config.current.tenant_id
    azure_rbac_enabled     = true
    admin_group_object_ids = var.aks_admin_group_object_ids
  }

  oms_agent {
    log_analytics_workspace_id      = azurerm_log_analytics_workspace.main.id
    msi_auth_for_monitoring_enabled = true
  }

  # Azure Monitor managed Prometheus -> North Europe workspace (DR.7)
  monitor_metrics {
    annotations_allowed = "kserve.io/*"
    labels_allowed      = "app,serving.kserve.io/inferenceservice"
  }

  key_vault_secrets_provider {
    secret_rotation_enabled  = true
    secret_rotation_interval = "5m"
  }

  maintenance_window_auto_upgrade {
    frequency   = "Weekly"
    interval    = 1
    duration    = 4
    day_of_week = "Saturday" # staggered from the primary (Sunday)
    start_time  = "01:00"
    utc_offset  = "+00:00"
  }

  tags = local.dr_tags

  lifecycle {
    precondition {
      condition     = var.dr_hub_firewall_private_ip != null && var.dr_hub_vnet_id != null
      error_message = "enable_dr = true requires dr_hub_vnet_id and dr_hub_firewall_private_ip: the DR AKS cluster egresses only through the North Europe hub firewall (userDefinedRouting). There is no load-balancer public-IP fallback, because Azure Policy denies public IPs. Set both variables (and allow the AKS egress FQDNs on that firewall), or set enable_dr = false."
    }
  }

  depends_on = [
    azurerm_role_assignment.aks_dr_network_contributor,
    azurerm_role_assignment.aks_dr_route_table,
    azurerm_subnet_route_table_association.dr,
    azurerm_subnet_network_security_group_association.dr,
    azurerm_virtual_network_peering.dr_to_dr_hub,
    azurerm_private_endpoint.dr,
  ]
}

# Warm standby: 2 nodes, scales out to the primary maximum on failover
resource "azurerm_kubernetes_cluster_node_pool" "inference_dr" {
  count                 = var.enable_dr ? 1 : 0
  name                  = "cpuinfer"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.dr[0].id
  mode                  = "User"
  vm_size               = var.aks_user_vm_size
  zones                 = var.availability_zones
  vnet_subnet_id        = azurerm_subnet.dr["snet-aks-user"].id
  auto_scaling_enabled  = true
  min_count             = 2
  max_count             = var.aks_user_node_count.max
  os_disk_type          = "Ephemeral"
  os_disk_size_gb       = 128
  max_pods              = 110

  node_labels = {
    "workload"       = "churn-inference"
    "kserve/enabled" = "true"
  }

  upgrade_settings {
    max_surge = "33%"
  }

  tags = local.dr_tags
}

# Same KServe workload identity, federated to the DR cluster's OIDC issuer
resource "azurerm_federated_identity_credential" "serving_dr" {
  count               = var.enable_dr ? 1 : 0
  name                = "fic-kserve-dr-${var.kserve_service_account}"
  resource_group_name = azurerm_resource_group.main.name
  parent_id           = azurerm_user_assigned_identity.serving.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = azurerm_kubernetes_cluster.dr[0].oidc_issuer_url
  subject             = "system:serviceaccount:${var.kserve_namespace}:${var.kserve_service_account}"
}

# Images are pulled from the ACR North Europe geo-replica
resource "azurerm_role_assignment" "aks_dr_kubelet_acrpull" {
  count                = var.enable_dr ? 1 : 0
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.dr[0].kubelet_identity[0].object_id
}

# =========================================================================
# DR.5 REDIS PASSIVE GEO-REPLICA (FEAST ONLINE STORE)
# Must match the primary SKU, size and shard count. Promote on failover by
# unlinking (DR runbook); or rebuild from Gold churn_scores (RTO ~2 h).
# Entra ID access policy assignments for id-serving are applied after
# promotion (runbook), because the geo-secondary is read-only.
# =========================================================================
resource "azurerm_redis_cache" "feast_online_dr" {
  count                         = var.enable_dr ? 1 : 0
  name                          = "redis-${local.dr_name_prefix}-${random_string.suffix.result}"
  location                      = azurerm_resource_group.dr.location
  resource_group_name           = azurerm_resource_group.dr.name
  sku_name                      = "Premium"
  family                        = "P"
  capacity                      = var.redis_capacity
  shard_count                   = var.redis_shard_count
  zones                         = var.availability_zones
  replicas_per_primary          = 1
  non_ssl_port_enabled          = false
  minimum_tls_version           = "1.2"
  public_network_access_enabled = false

  redis_configuration {
    maxmemory_policy                        = "volatile-lru"
    active_directory_authentication_enabled = true
  }

  patch_schedule {
    day_of_week    = "Saturday"
    start_hour_utc = 2
  }

  tags = local.dr_tags
}

resource "azurerm_redis_linked_server" "feast_online_dr" {
  count                       = var.enable_dr ? 1 : 0
  target_redis_cache_name     = azurerm_redis_cache.feast_online.name
  resource_group_name         = azurerm_redis_cache.feast_online.resource_group_name
  linked_redis_cache_id       = azurerm_redis_cache.feast_online_dr[0].id
  linked_redis_cache_location = azurerm_redis_cache.feast_online_dr[0].location
  server_role                 = "Secondary"
}

resource "azurerm_private_endpoint" "redis_dr" {
  count               = var.enable_dr ? 1 : 0
  name                = "pe-redis-${local.dr_name_prefix}"
  location            = azurerm_resource_group.dr.location
  resource_group_name = azurerm_resource_group.dr.name
  subnet_id           = azurerm_subnet.dr["snet-private-endpoints"].id

  private_service_connection {
    name                           = "psc-redis-dr"
    private_connection_resource_id = azurerm_redis_cache.feast_online_dr[0].id
    subresource_names              = ["redisCache"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-redis-dr"
    private_dns_zone_ids = [azurerm_private_dns_zone.dr["redis"].id]
  }

  tags = local.dr_tags
}

# =========================================================================
# DR.6 APIM REGIONAL UNIT: public IP for the additional_location (main.tf)
# =========================================================================
resource "azurerm_public_ip" "apim_dr" {
  count               = var.enable_dr ? 1 : 0
  name                = "pip-apim-${local.dr_name_prefix}"
  location            = azurerm_resource_group.dr.location
  resource_group_name = azurerm_resource_group.dr.name
  allocation_method   = "Static"
  sku                 = "Standard"
  zones               = var.availability_zones
  domain_name_label   = "apim-${local.dr_name_prefix}-${random_string.suffix.result}"
  tags                = local.dr_tags
}

# =========================================================================
# DR.7 MANAGED PROMETHEUS FOR THE DR CLUSTER
# Same wiring as the primary (main.tf, section 3), in North Europe: a regional
# Azure Monitor workspace keeps DR metrics available when West Europe is down.
# The DCE must be in the cluster's region. Managed Grafana (West Europe) reads
# both workspaces (azure_monitor_workspace_integrations in main.tf).
# =========================================================================
resource "azurerm_monitor_workspace" "prometheus_dr" {
  count               = var.enable_dr ? 1 : 0
  name                = "amw-${local.dr_name_prefix}"
  location            = azurerm_resource_group.dr.location
  resource_group_name = azurerm_resource_group.dr.name
  tags                = local.dr_tags
}

resource "azurerm_monitor_data_collection_endpoint" "prometheus_dr" {
  count               = var.enable_dr ? 1 : 0
  name                = "dce-prom-${local.dr_name_prefix}"
  location            = azurerm_resource_group.dr.location
  resource_group_name = azurerm_resource_group.dr.name
  kind                = "Linux"
  tags                = local.dr_tags
}

resource "azurerm_monitor_data_collection_rule" "prometheus_dr" {
  count                       = var.enable_dr ? 1 : 0
  name                        = "dcr-prom-${local.dr_name_prefix}"
  location                    = azurerm_resource_group.dr.location
  resource_group_name         = azurerm_resource_group.dr.name
  data_collection_endpoint_id = azurerm_monitor_data_collection_endpoint.prometheus_dr[0].id
  kind                        = "Linux"

  destinations {
    monitor_account {
      monitor_account_id = azurerm_monitor_workspace.prometheus_dr[0].id
      name               = "MonitoringAccount1"
    }
  }

  data_flow {
    streams      = ["Microsoft-PrometheusMetrics"]
    destinations = ["MonitoringAccount1"]
  }

  data_sources {
    prometheus_forwarder {
      streams = ["Microsoft-PrometheusMetrics"]
      name    = "PrometheusDataSource"
    }
  }

  tags = local.dr_tags
}

resource "azurerm_monitor_data_collection_rule_association" "aks_dr_prometheus" {
  count                   = var.enable_dr ? 1 : 0
  name                    = "dcra-prom-aks-dr"
  target_resource_id      = azurerm_kubernetes_cluster.dr[0].id
  data_collection_rule_id = azurerm_monitor_data_collection_rule.prometheus_dr[0].id
}

resource "azurerm_role_assignment" "grafana_prometheus_dr_reader" {
  count                = var.enable_dr ? 1 : 0
  scope                = azurerm_monitor_workspace.prometheus_dr[0].id
  role_definition_name = "Monitoring Data Reader"
  principal_id         = azurerm_dashboard_grafana.main.identity[0].principal_id
}
