# =========================================================================
# CUSTOMER CHURN PREDICTION PLATFORM - AZURE INFRASTRUCTURE (TERRAFORM)
# Pattern : Predictive ML (LightGBM), hybrid batch + real-time inference
# Region  : West Europe (3 AZs) primary, North Europe DR (warm standby)
# =========================================================================

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
      # 4.62.0 is the lowest 4.x release that validates this configuration
      # (bgp_enabled on azurerm_virtual_network_gateway); bisected with
      # terraform validate against 4.50.0-4.81.0.
      version = "~> 4.62"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Remote state. Backend blocks cannot use variables: supply real values with
  #   terraform init -backend-config="resource_group_name=..." \
  #                  -backend-config="storage_account_name=..." ...
  backend "azurerm" {
    resource_group_name  = "rg-tfstate-placeholder"
    storage_account_name = "sttfstateplaceholder"
    container_name       = "tfstate"
    key                  = "churn-platform/prod.tfstate"
    use_oidc             = true
    use_azuread_auth     = true
  }
}

provider "azurerm" {
  subscription_id     = var.subscription_id
  storage_use_azuread = true # shared keys are disabled on all storage accounts

  features {
    key_vault {
      purge_soft_delete_on_destroy = false
    }
    resource_group {
      prevent_deletion_if_contains_resources = true
    }
  }
}

data "azurerm_client_config" "current" {}

resource "random_string" "suffix" {
  length  = 5
  upper   = false
  special = false
}

locals {
  name_prefix = "${var.project}-${var.environment}"
  # Globally unique, alphanumeric names (storage, key vault, ACR)
  compact_name = "${var.project}${var.environment}${random_string.suffix.result}"

  tags = merge(var.tags, {
    Project     = "Customer-Churn-Prediction"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Workload    = "Predictive-ML"
  })
}

# =========================================================================
# 1. RESOURCE GROUP
# =========================================================================
resource "azurerm_resource_group" "main" {
  name     = "rg-${local.name_prefix}-${var.location}"
  location = var.location
  tags     = local.tags
}

# =========================================================================
# 2. NETWORKING: HUB-SPOKE VNETS
# =========================================================================
resource "azurerm_virtual_network" "hub" {
  name                = "vnet-hub-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  address_space       = [var.hub_vnet_cidr]
  tags                = local.tags
}

resource "azurerm_subnet" "hub" {
  for_each             = var.hub_subnets
  name                 = each.key
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.hub.name
  address_prefixes     = [each.value]
}

resource "azurerm_virtual_network" "spoke" {
  name                = "vnet-spoke-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  address_space       = [var.spoke_vnet_cidr]
  tags                = local.tags
}

resource "azurerm_subnet" "spoke" {
  for_each             = var.spoke_subnets
  name                 = each.key
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.spoke.name
  address_prefixes     = [each.value.cidr]

  private_endpoint_network_policies = each.key == "snet-private-endpoints" ? "Enabled" : "Disabled"
  # App Gateway Private Link NAT IPs require PLS network policies off on their subnet
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

resource "azurerm_virtual_network_peering" "hub_to_spoke" {
  name                         = "peer-hub-to-spoke"
  resource_group_name          = azurerm_resource_group.main.name
  virtual_network_name         = azurerm_virtual_network.hub.name
  remote_virtual_network_id    = azurerm_virtual_network.spoke.id
  allow_forwarded_traffic      = true
  allow_gateway_transit        = var.enable_vpn_gateway
  allow_virtual_network_access = true
}

resource "azurerm_virtual_network_peering" "spoke_to_hub" {
  name                         = "peer-spoke-to-hub"
  resource_group_name          = azurerm_resource_group.main.name
  virtual_network_name         = azurerm_virtual_network.spoke.name
  remote_virtual_network_id    = azurerm_virtual_network.hub.id
  allow_forwarded_traffic      = true
  use_remote_gateways          = var.enable_vpn_gateway
  allow_virtual_network_access = true

  depends_on = [azurerm_virtual_network_gateway.hub]
}

# -------------------------------------------------------------------------
# 2a. Hub: Azure Firewall (egress control), Bastion, VPN gateway
# -------------------------------------------------------------------------
resource "azurerm_public_ip" "firewall" {
  name                = "pip-afw-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Static"
  sku                 = "Standard"
  zones               = var.availability_zones
  tags                = local.tags
}

resource "azurerm_firewall_policy" "hub" {
  name                     = "afwp-${local.name_prefix}"
  location                 = azurerm_resource_group.main.location
  resource_group_name      = azurerm_resource_group.main.name
  sku                      = "Premium"
  threat_intelligence_mode = "Deny"

  intrusion_detection {
    mode = "Deny"
  }

  tags = local.tags
}

resource "azurerm_firewall_policy_rule_collection_group" "aks_egress" {
  name               = "rcg-aks-egress"
  firewall_policy_id = azurerm_firewall_policy.hub.id
  priority           = 200

  network_rule_collection {
    name     = "aks-network"
    priority = 210
    action   = "Allow"

    rule {
      name                  = "aks-tunnel-udp"
      protocols             = ["UDP"]
      source_addresses      = [var.spoke_vnet_cidr]
      destination_addresses = ["AzureCloud.${var.location}"]
      destination_ports     = ["1194"]
    }

    rule {
      name                  = "aks-tunnel-tcp"
      protocols             = ["TCP"]
      source_addresses      = [var.spoke_vnet_cidr]
      destination_addresses = ["AzureCloud.${var.location}"]
      destination_ports     = ["9000"]
    }

    rule {
      name              = "ntp"
      protocols         = ["UDP"]
      source_addresses  = [var.spoke_vnet_cidr]
      destination_fqdns = ["ntp.ubuntu.com"]
      destination_ports = ["123"]
    }
  }

  application_rule_collection {
    name     = "aks-application"
    priority = 220
    action   = "Allow"

    rule {
      name                  = "aks-fqdn-tag"
      source_addresses      = [var.spoke_vnet_cidr]
      destination_fqdn_tags = ["AzureKubernetesService"]
      protocols {
        type = "Https"
        port = 443
      }
    }

    rule {
      name             = "azure-monitor-and-ml"
      source_addresses = [var.spoke_vnet_cidr]
      destination_fqdns = [
        "*.ods.opinsights.azure.com",
        "*.oms.opinsights.azure.com",
        "*.monitoring.azure.com",
        "*.handler.control.monitor.azure.com",
        "*.azureml.ms",
        "*.mcr.microsoft.com",
        "pypi.org",
        "files.pythonhosted.org",
      ]
      protocols {
        type = "Https"
        port = 443
      }
    }
  }
}

resource "azurerm_firewall" "hub" {
  name                = "afw-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku_name            = "AZFW_VNet"
  sku_tier            = "Premium"
  firewall_policy_id  = azurerm_firewall_policy.hub.id
  zones               = var.availability_zones

  ip_configuration {
    name                 = "ipconfig"
    subnet_id            = azurerm_subnet.hub["AzureFirewallSubnet"].id
    public_ip_address_id = azurerm_public_ip.firewall.id
  }

  tags = local.tags
}

resource "azurerm_public_ip" "bastion" {
  name                = "pip-bas-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Static"
  sku                 = "Standard"
  zones               = var.availability_zones
  tags                = local.tags
}

resource "azurerm_bastion_host" "hub" {
  name                = "bas-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "Standard"
  tunneling_enabled   = true

  ip_configuration {
    name                 = "ipconfig"
    subnet_id            = azurerm_subnet.hub["AzureBastionSubnet"].id
    public_ip_address_id = azurerm_public_ip.bastion.id
  }

  tags = local.tags
}

resource "azurerm_public_ip" "vpn" {
  count               = var.enable_vpn_gateway ? 1 : 0
  name                = "pip-vgw-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Static"
  sku                 = "Standard"
  zones               = var.availability_zones
  tags                = local.tags
}

# Site-to-site connectivity to on-prem CRM / Billing systems
resource "azurerm_virtual_network_gateway" "hub" {
  count               = var.enable_vpn_gateway ? 1 : 0
  name                = "vgw-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  type                = "Vpn"
  vpn_type            = "RouteBased"
  sku                 = "VpnGw2AZ"
  generation          = "Generation2"
  active_active       = false
  bgp_enabled         = true

  ip_configuration {
    name                 = "vnetGatewayConfig"
    public_ip_address_id = azurerm_public_ip.vpn[0].id
    subnet_id            = azurerm_subnet.hub["GatewaySubnet"].id
  }

  tags = local.tags
}

# -------------------------------------------------------------------------
# 2b. Spoke: forced tunnelling of AKS egress through Azure Firewall
# -------------------------------------------------------------------------
resource "azurerm_route_table" "spoke_egress" {
  name                = "rt-spoke-egress-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  route {
    name                   = "default-via-firewall"
    address_prefix         = "0.0.0.0/0"
    next_hop_type          = "VirtualAppliance"
    next_hop_in_ip_address = azurerm_firewall.hub.ip_configuration[0].private_ip_address
  }

  tags = local.tags
}

resource "azurerm_subnet_route_table_association" "spoke" {
  for_each       = { for k, v in var.spoke_subnets : k => v if v.udr }
  subnet_id      = azurerm_subnet.spoke[each.key].id
  route_table_id = azurerm_route_table.spoke_egress.id
}

# -------------------------------------------------------------------------
# 2c. Network Security Groups (one per spoke subnet)
# -------------------------------------------------------------------------
locals {
  nsg_rules = {
    snet-apim = [
      { name = "Allow-APIM-Management", priority = 100, direction = "Inbound", protocol = "Tcp", source = "ApiManagement", destination = "VirtualNetwork", port = "3443" },
      { name = "Allow-AzureLB-Health", priority = 110, direction = "Inbound", protocol = "Tcp", source = "AzureLoadBalancer", destination = "VirtualNetwork", port = "6390" },
      { name = "Allow-HTTPS-From-VNet", priority = 120, direction = "Inbound", protocol = "Tcp", source = "VirtualNetwork", destination = "VirtualNetwork", port = "443" },
      { name = "Allow-Storage-Out", priority = 100, direction = "Outbound", protocol = "Tcp", source = "VirtualNetwork", destination = "Storage", port = "443" },
      { name = "Allow-KeyVault-Out", priority = 110, direction = "Outbound", protocol = "Tcp", source = "VirtualNetwork", destination = "AzureKeyVault", port = "443" },
      { name = "Allow-Monitor-Out", priority = 120, direction = "Outbound", protocol = "Tcp", source = "VirtualNetwork", destination = "AzureMonitor", port = "443" },
      { name = "Allow-Sql-Out", priority = 130, direction = "Outbound", protocol = "Tcp", source = "VirtualNetwork", destination = "Sql", port = "1433" },
    ]
    snet-aks-user = [
      { name = "Allow-APIM-To-Ingress", priority = 100, direction = "Inbound", protocol = "Tcp", source = var.spoke_subnets["snet-apim"].cidr, destination = "VirtualNetwork", port = "443" },
    ]
    # App Gateway v2: control-plane ports from GatewayManager and LB probes are mandatory.
    # Front Door traffic arrives via Private Link NAT IPs in snet-appgw-pl (VirtualNetwork).
    snet-appgw = [
      { name = "Allow-GatewayManager", priority = 100, direction = "Inbound", protocol = "Tcp", source = "GatewayManager", destination = "*", port = "65200-65535" },
      { name = "Allow-AzureLB", priority = 110, direction = "Inbound", protocol = "*", source = "AzureLoadBalancer", destination = "*", port = "*" },
      { name = "Allow-HTTPS-From-VNet", priority = 120, direction = "Inbound", protocol = "Tcp", source = "VirtualNetwork", destination = "VirtualNetwork", port = "443" },
      { name = "Deny-Internet-In", priority = 4000, direction = "Inbound", protocol = "*", source = "Internet", destination = "*", port = "*" },
    ]
    snet-private-endpoints = [
      { name = "Allow-VNet-To-PE", priority = 100, direction = "Inbound", protocol = "Tcp", source = "VirtualNetwork", destination = "VirtualNetwork", port = "*" },
      { name = "Deny-Internet-In", priority = 4000, direction = "Inbound", protocol = "*", source = "Internet", destination = "*", port = "*" },
    ]
    snet-aml = [
      { name = "Allow-AML-Batch", priority = 100, direction = "Inbound", protocol = "Tcp", source = "BatchNodeManagement", destination = "VirtualNetwork", port = "29876-29877" },
      { name = "Allow-AML-Service", priority = 110, direction = "Inbound", protocol = "Tcp", source = "AzureMachineLearning", destination = "VirtualNetwork", port = "44224" },
    ]
  }
}

resource "azurerm_network_security_group" "spoke" {
  for_each            = var.spoke_subnets
  name                = "nsg-${each.key}-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  dynamic "security_rule" {
    for_each = lookup(local.nsg_rules, each.key, [])
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

  tags = local.tags
}

resource "azurerm_subnet_network_security_group_association" "spoke" {
  for_each                  = var.spoke_subnets
  subnet_id                 = azurerm_subnet.spoke[each.key].id
  network_security_group_id = azurerm_network_security_group.spoke[each.key].id
}

# -------------------------------------------------------------------------
# 2d. Private DNS zones (linked to hub + spoke)
# -------------------------------------------------------------------------
locals {
  private_dns_zones = {
    blob       = "privatelink.blob.core.windows.net"
    dfs        = "privatelink.dfs.core.windows.net"
    vault      = "privatelink.vaultcore.azure.net"
    acr        = "privatelink.azurecr.io"
    redis      = "privatelink.redis.cache.windows.net"
    eventhub   = "privatelink.servicebus.windows.net"
    aml_api    = "privatelink.api.azureml.ms"
    aml_nb     = "privatelink.notebooks.azure.net"
    databricks = "privatelink.azuredatabricks.net"
    adf        = "privatelink.datafactory.azure.net"
    purview    = "privatelink.purview.azure.com"
    purview_ui = "privatelink.purviewstudio.azure.com"
  }

  dns_vnet_links = {
    for pair in setproduct(keys(local.private_dns_zones), ["hub", "spoke"]) :
    "${pair[0]}-${pair[1]}" => { zone = pair[0], vnet = pair[1] }
  }
}

resource "azurerm_private_dns_zone" "this" {
  for_each            = local.private_dns_zones
  name                = each.value
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "this" {
  for_each              = local.dns_vnet_links
  name                  = "link-${each.key}"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.this[each.value.zone].name
  virtual_network_id    = each.value.vnet == "hub" ? azurerm_virtual_network.hub.id : azurerm_virtual_network.spoke.id
  registration_enabled  = false
  tags                  = local.tags
}

# =========================================================================
# 3. OBSERVABILITY: LOG ANALYTICS, APP INSIGHTS, MANAGED PROMETHEUS/GRAFANA
# =========================================================================
resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days
  tags                = local.tags
}

resource "azurerm_application_insights" "main" {
  name                = "appi-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  tags                = local.tags
}

resource "azurerm_monitor_workspace" "prometheus" {
  name                = "amw-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

resource "azurerm_monitor_data_collection_endpoint" "prometheus" {
  name                = "dce-prom-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "Linux"
  tags                = local.tags
}

resource "azurerm_monitor_data_collection_rule" "prometheus" {
  name                        = "dcr-prom-${local.name_prefix}"
  location                    = azurerm_resource_group.main.location
  resource_group_name         = azurerm_resource_group.main.name
  data_collection_endpoint_id = azurerm_monitor_data_collection_endpoint.prometheus.id
  kind                        = "Linux"

  destinations {
    monitor_account {
      monitor_account_id = azurerm_monitor_workspace.prometheus.id
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

  tags = local.tags
}

resource "azurerm_monitor_data_collection_rule_association" "aks_prometheus" {
  name                    = "dcra-prom-aks"
  target_resource_id      = azurerm_kubernetes_cluster.main.id
  data_collection_rule_id = azurerm_monitor_data_collection_rule.prometheus.id
}

resource "azurerm_dashboard_grafana" "main" {
  name                              = "amg-${var.project}-${var.environment}"
  location                          = azurerm_resource_group.main.location
  resource_group_name               = azurerm_resource_group.main.name
  grafana_major_version             = "11"
  sku                               = "Standard"
  zone_redundancy_enabled           = true
  public_network_access_enabled     = false
  api_key_enabled                   = false
  deterministic_outbound_ip_enabled = true

  identity {
    type = "SystemAssigned"
  }

  azure_monitor_workspace_integrations {
    resource_id = azurerm_monitor_workspace.prometheus.id
  }

  # DR AKS managed Prometheus (North Europe workspace, dr.tf DR.7)
  dynamic "azure_monitor_workspace_integrations" {
    for_each = azurerm_monitor_workspace.prometheus_dr
    content {
      resource_id = azure_monitor_workspace_integrations.value.id
    }
  }

  tags = local.tags
}

# =========================================================================
# 4. IDENTITIES (MANAGED / WORKLOAD IDENTITY)
# =========================================================================
resource "azurerm_user_assigned_identity" "cmk" {
  name                = "id-cmk-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

resource "azurerm_user_assigned_identity" "aks" {
  name                = "id-aks-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

resource "azurerm_user_assigned_identity" "aml" {
  name                = "id-aml-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

# KServe Transformer/Predictor pods (Feast lookup, model artifacts, secrets)
resource "azurerm_user_assigned_identity" "serving" {
  name                = "id-serving-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

resource "azurerm_federated_identity_credential" "serving" {
  name                = "fic-kserve-${var.kserve_service_account}"
  resource_group_name = azurerm_resource_group.main.name
  parent_id           = azurerm_user_assigned_identity.serving.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = azurerm_kubernetes_cluster.main.oidc_issuer_url
  subject             = "system:serviceaccount:${var.kserve_namespace}:${var.kserve_service_account}"
}

# =========================================================================
# 5. KEY VAULT (CMK, PURGE PROTECTION, RBAC, PRIVATE)
# =========================================================================
resource "azurerm_key_vault" "main" {
  name                          = "kv-${local.compact_name}"
  location                      = azurerm_resource_group.main.location
  resource_group_name           = azurerm_resource_group.main.name
  tenant_id                     = data.azurerm_client_config.current.tenant_id
  sku_name                      = "premium"
  rbac_authorization_enabled    = true
  purge_protection_enabled      = true
  soft_delete_retention_days    = 90
  public_network_access_enabled = length(var.deployer_allowed_ips) > 0

  network_acls {
    default_action = "Deny"
    bypass         = "AzureServices"
    ip_rules       = var.deployer_allowed_ips
  }

  tags = local.tags
}

resource "azurerm_role_assignment" "deployer_kv_crypto_officer" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Crypto Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_key_vault_key" "cmk" {
  name         = "cmk-${var.project}-data"
  key_vault_id = azurerm_key_vault.main.id
  key_type     = "RSA-HSM"
  key_size     = 3072
  key_opts     = ["wrapKey", "unwrapKey"]

  rotation_policy {
    automatic {
      time_before_expiry = "P30D"
    }
    expire_after         = "P365D"
    notify_before_expiry = "P29D"
  }

  depends_on = [azurerm_role_assignment.deployer_kv_crypto_officer]
}

resource "azurerm_role_assignment" "cmk_crypto_user" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Crypto Service Encryption User"
  principal_id         = azurerm_user_assigned_identity.cmk.principal_id
}

# =========================================================================
# 6. DATA LAKE: ADLS GEN2 (HNS, CMK, PRIVATE) - DELTA MEDALLION + FEAST OFFLINE
# =========================================================================
resource "azurerm_storage_account" "lake" {
  name                              = "stlake${local.compact_name}"
  location                          = azurerm_resource_group.main.location
  resource_group_name               = azurerm_resource_group.main.name
  account_kind                      = "StorageV2"
  account_tier                      = "Standard"
  account_replication_type          = "GZRS" # zone-redundant + geo copy to DR region
  is_hns_enabled                    = true
  min_tls_version                   = "TLS1_2"
  https_traffic_only_enabled        = true
  public_network_access_enabled     = false
  shared_access_key_enabled         = false
  allow_nested_items_to_be_public   = false
  infrastructure_encryption_enabled = true

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.cmk.id]
  }

  customer_managed_key {
    key_vault_key_id          = azurerm_key_vault_key.cmk.versionless_id
    user_assigned_identity_id = azurerm_user_assigned_identity.cmk.id
  }

  blob_properties {
    delete_retention_policy {
      days = 30
    }
    container_delete_retention_policy {
      days = 30
    }
  }

  network_rules {
    default_action = "Deny"
    bypass         = ["AzureServices", "Logging", "Metrics"]
  }

  tags = local.tags

  depends_on = [azurerm_role_assignment.cmk_crypto_user]
}

resource "azurerm_storage_data_lake_gen2_filesystem" "lake" {
  for_each           = toset(var.lake_containers)
  name               = each.value
  storage_account_id = azurerm_storage_account.lake.id

  depends_on = [azurerm_private_endpoint.this]
}

# Azure ML default storage (HNS-disabled; AML does not support HNS for its default store)
resource "azurerm_storage_account" "aml" {
  name                            = "staml${local.compact_name}"
  location                        = azurerm_resource_group.main.location
  resource_group_name             = azurerm_resource_group.main.name
  account_kind                    = "StorageV2"
  account_tier                    = "Standard"
  account_replication_type        = "ZRS"
  min_tls_version                 = "TLS1_2"
  public_network_access_enabled   = false
  shared_access_key_enabled       = false
  allow_nested_items_to_be_public = false

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.cmk.id]
  }

  customer_managed_key {
    key_vault_key_id          = azurerm_key_vault_key.cmk.versionless_id
    user_assigned_identity_id = azurerm_user_assigned_identity.cmk.id
  }

  network_rules {
    default_action = "Deny"
    bypass         = ["AzureServices"]
  }

  tags = local.tags

  depends_on = [azurerm_role_assignment.cmk_crypto_user]
}

# =========================================================================
# 7. INGESTION: DATA FACTORY (BATCH) + EVENT HUBS (STREAMING)
# =========================================================================
resource "azurerm_data_factory" "main" {
  name                            = "adf-${local.name_prefix}-${random_string.suffix.result}"
  location                        = azurerm_resource_group.main.location
  resource_group_name             = azurerm_resource_group.main.name
  managed_virtual_network_enabled = true
  public_network_enabled          = false

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

resource "azurerm_eventhub_namespace" "main" {
  name                          = "evhns-${local.name_prefix}-${random_string.suffix.result}"
  location                      = azurerm_resource_group.main.location
  resource_group_name           = azurerm_resource_group.main.name
  sku                           = "Standard"
  capacity                      = var.eventhub_capacity
  auto_inflate_enabled          = true
  maximum_throughput_units      = var.eventhub_capacity * 3
  public_network_access_enabled = false
  local_authentication_enabled  = false
  minimum_tls_version           = "1.2"

  # Capture writes to the lake with this identity (no SAS; shared keys are off)
  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

resource "azurerm_role_assignment" "eventhub_capture_lake" {
  scope                = azurerm_storage_account.lake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_eventhub_namespace.main.identity[0].principal_id
}

# Event Hubs Capture lands every raw event in Bronze (Avro) for offline/online
# parity, prediction-log audit and replay (system-design.md, flow C).
resource "azurerm_eventhub" "this" {
  for_each          = var.event_hubs
  name              = each.key
  namespace_id      = azurerm_eventhub_namespace.main.id
  partition_count   = each.value.partitions
  message_retention = each.value.retention_days

  capture_description {
    enabled             = true
    encoding            = "Avro"
    interval_in_seconds = 300
    size_limit_in_bytes = 314572800
    skip_empty_archives = true

    destination {
      name                        = "EventHubArchive.AzureBlockBlob"
      archive_name_format         = "eventhub-capture/{Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}"
      blob_container_name         = "bronze"
      storage_account_id          = azurerm_storage_account.lake.id
      storage_authentication_type = "SystemAssigned"
    }
  }

  depends_on = [
    azurerm_role_assignment.eventhub_capture_lake,
    azurerm_storage_data_lake_gen2_filesystem.lake,
  ]
}

resource "azurerm_eventhub_consumer_group" "streaming_features" {
  for_each            = { for k, v in var.event_hubs : k => v if k != "churn-score-feed" }
  name                = "databricks-structured-streaming"
  namespace_name      = azurerm_eventhub_namespace.main.name
  eventhub_name       = azurerm_eventhub.this[each.key].name
  resource_group_name = azurerm_resource_group.main.name
}

# =========================================================================
# 8. FEAST ONLINE STORE: AZURE CACHE FOR REDIS PREMIUM (ZONE-REDUNDANT)
# =========================================================================
locals {
  # Azure does not support data persistence on caches that use passive
  # geo-replication, so AOF is applied only when the DR geo-replica is off
  # (enable_dr = false, e.g. non-prod). With DR on, durability comes from the
  # zone-redundant replica, the North Europe geo-replica and the rebuild from
  # Gold churn_scores (system-design.md, sections 9.4 and 12.2).
  redis_aof_enabled = var.redis_aof_persistence_enabled && !var.enable_dr
}

# Redis identity used for managed-identity-based persistence auth (no storage keys)
resource "azurerm_user_assigned_identity" "redis" {
  name                = "id-redis-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

# Dedicated AOF persistence account: Azure requires one storage account per
# cache, in the cache region, without HNS (page blobs), so the lake cannot be
# reused. Blob soft delete stays off (AOF rewrites would bill deleted blobs).
# Public network access is "enabled from selected networks" with no network or
# IP rules: only the trusted-service exception (Redis via managed identity)
# gets through. This is the one account that needs an Azure Policy exemption
# from "storage accounts should disable public network access", because the
# Premium Redis persistence writer does not use private endpoints.
resource "azurerm_storage_account" "redis_persistence" {
  count                           = local.redis_aof_enabled ? 1 : 0
  name                            = "stredis${local.compact_name}"
  location                        = azurerm_resource_group.main.location
  resource_group_name             = azurerm_resource_group.main.name
  account_kind                    = "StorageV2"
  account_tier                    = "Standard"
  account_replication_type        = "ZRS"
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  public_network_access_enabled   = true # see comment above: default Deny, trusted services only
  shared_access_key_enabled       = false
  allow_nested_items_to_be_public = false

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.cmk.id]
  }

  customer_managed_key {
    key_vault_key_id          = azurerm_key_vault_key.cmk.versionless_id
    user_assigned_identity_id = azurerm_user_assigned_identity.cmk.id
  }

  network_rules {
    default_action = "Deny"
    bypass         = ["AzureServices"]
  }

  tags = local.tags

  depends_on = [azurerm_role_assignment.cmk_crypto_user]
}

resource "azurerm_role_assignment" "redis_persistence_writer" {
  count                = local.redis_aof_enabled ? 1 : 0
  scope                = azurerm_storage_account.redis_persistence[0].id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.redis.principal_id
}

resource "azurerm_redis_cache" "feast_online" {
  name                          = "redis-${local.name_prefix}-${random_string.suffix.result}"
  location                      = azurerm_resource_group.main.location
  resource_group_name           = azurerm_resource_group.main.name
  sku_name                      = "Premium"
  family                        = "P"
  capacity                      = var.redis_capacity
  shard_count                   = var.redis_shard_count
  zones                         = var.availability_zones
  replicas_per_primary          = 1 # passive geo-replication (DR) supports at most one replica
  non_ssl_port_enabled          = false
  minimum_tls_version           = "1.2"
  public_network_access_enabled = false

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.redis.id]
  }

  redis_configuration {
    maxmemory_policy                        = "volatile-lru"
    active_directory_authentication_enabled = true

    # AOF persistence (write log flushed every second) with managed-identity auth
    aof_backup_enabled                     = local.redis_aof_enabled
    aof_storage_connection_string_0        = local.redis_aof_enabled ? "BlobEndpoint=${azurerm_storage_account.redis_persistence[0].primary_blob_endpoint};" : null
    data_persistence_authentication_method = local.redis_aof_enabled ? "ManagedIdentity" : null
    storage_account_subscription_id        = local.redis_aof_enabled ? data.azurerm_client_config.current.subscription_id : null
  }

  patch_schedule {
    day_of_week    = "Sunday"
    start_hour_utc = 2
  }

  tags = local.tags

  depends_on = [azurerm_role_assignment.redis_persistence_writer]
}

# =========================================================================
# 9. CONTAINER REGISTRY (PREMIUM, ZONE-REDUNDANT, GEO-REPLICATED TO DR)
# =========================================================================
resource "azurerm_container_registry" "main" {
  name                          = "acr${local.compact_name}"
  location                      = azurerm_resource_group.main.location
  resource_group_name           = azurerm_resource_group.main.name
  sku                           = "Premium"
  admin_enabled                 = false
  public_network_access_enabled = false
  zone_redundancy_enabled       = true
  network_rule_bypass_option    = "AzureServices"
  # Regional data endpoints (<registry>.<region>.data.azurecr.io): each region's
  # registry private endpoint maps them in that region's privatelink zone, so the
  # DR cluster pulls layers from the North Europe replica (dr.tf, DR.3).
  data_endpoint_enabled = true

  georeplications {
    location                = var.dr_location
    zone_redundancy_enabled = true
    tags                    = local.tags
  }

  tags = local.tags
}

# =========================================================================
# 10. AZURE MACHINE LEARNING: WORKSPACE + CPU CLUSTERS (MLFLOW REGISTRY)
# =========================================================================
resource "azurerm_machine_learning_workspace" "main" {
  name                           = "mlw-${local.name_prefix}"
  location                       = azurerm_resource_group.main.location
  resource_group_name            = azurerm_resource_group.main.name
  application_insights_id        = azurerm_application_insights.main.id
  key_vault_id                   = azurerm_key_vault.main.id
  storage_account_id             = azurerm_storage_account.aml.id
  container_registry_id          = azurerm_container_registry.main.id
  public_network_access_enabled  = false
  high_business_impact           = true
  image_build_compute_name       = "cpu-training"
  primary_user_assigned_identity = azurerm_user_assigned_identity.aml.id

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aml.id]
  }

  tags = local.tags

  depends_on = [azurerm_role_assignment.aml_rg_contributor]
}

resource "azurerm_machine_learning_compute_cluster" "training" {
  name                          = "cpu-training"
  location                      = azurerm_resource_group.main.location
  machine_learning_workspace_id = azurerm_machine_learning_workspace.main.id
  vm_priority                   = "Dedicated"
  vm_size                       = var.aml_training_vm_size
  subnet_resource_id            = azurerm_subnet.spoke["snet-aml"].id
  node_public_ip_enabled        = false
  local_auth_enabled            = false

  scale_settings {
    min_node_count                       = 0
    max_node_count                       = var.aml_training_max_nodes
    scale_down_nodes_after_idle_duration = "PT15M"
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aml.id]
  }

  tags = local.tags
}

resource "azurerm_machine_learning_compute_cluster" "tuning" {
  name                          = "cpu-tuning-spot"
  location                      = azurerm_resource_group.main.location
  machine_learning_workspace_id = azurerm_machine_learning_workspace.main.id
  vm_priority                   = var.aml_tuning_low_priority ? "LowPriority" : "Dedicated"
  vm_size                       = var.aml_tuning_vm_size
  subnet_resource_id            = azurerm_subnet.spoke["snet-aml"].id
  node_public_ip_enabled        = false
  local_auth_enabled            = false

  scale_settings {
    min_node_count                       = 0
    max_node_count                       = var.aml_tuning_max_nodes
    scale_down_nodes_after_idle_duration = "PT5M"
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aml.id]
  }

  tags = local.tags
}

# Daily batch scoring of 18M customers (parallel run step + TreeSHAP), 03:30 CET
resource "azurerm_machine_learning_compute_cluster" "batch" {
  name                          = "cpu-batch"
  location                      = azurerm_resource_group.main.location
  machine_learning_workspace_id = azurerm_machine_learning_workspace.main.id
  vm_priority                   = "Dedicated" # 06:00 CET SLA: no spot eviction risk
  vm_size                       = var.aml_batch_vm_size
  subnet_resource_id            = azurerm_subnet.spoke["snet-aml"].id
  node_public_ip_enabled        = false
  local_auth_enabled            = false

  scale_settings {
    min_node_count                       = 0
    max_node_count                       = var.aml_batch_max_nodes
    scale_down_nodes_after_idle_duration = "PT10M"
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aml.id]
  }

  tags = local.tags
}

# =========================================================================
# 11. AZURE DATABRICKS (VNET-INJECTED, NO PUBLIC IP, PRIVATE LINK)
# =========================================================================
resource "azurerm_databricks_workspace" "main" {
  name                                  = "dbw-${local.name_prefix}"
  location                              = azurerm_resource_group.main.location
  resource_group_name                   = azurerm_resource_group.main.name
  sku                                   = "premium"
  managed_resource_group_name           = "rg-${local.name_prefix}-dbw-managed"
  public_network_access_enabled         = false
  network_security_group_rules_required = "NoAzureDatabricksRules"
  infrastructure_encryption_enabled     = true

  custom_parameters {
    no_public_ip                                         = true
    virtual_network_id                                   = azurerm_virtual_network.spoke.id
    public_subnet_name                                   = azurerm_subnet.spoke["snet-databricks-public"].name
    private_subnet_name                                  = azurerm_subnet.spoke["snet-databricks-private"].name
    public_subnet_network_security_group_association_id  = azurerm_subnet_network_security_group_association.spoke["snet-databricks-public"].id
    private_subnet_network_security_group_association_id = azurerm_subnet_network_security_group_association.spoke["snet-databricks-private"].id
  }

  tags = local.tags
}

# Unity Catalog access to the lake via managed identity
resource "azurerm_databricks_access_connector" "main" {
  name                = "dbac-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

# =========================================================================
# 12. PRIVATE ENDPOINTS FOR ALL PAAS SERVICES
# =========================================================================
locals {
  private_endpoints = {
    lake-blob      = { resource_id = azurerm_storage_account.lake.id, subresource = "blob", zones = ["blob"] }
    lake-dfs       = { resource_id = azurerm_storage_account.lake.id, subresource = "dfs", zones = ["dfs"] }
    aml-blob       = { resource_id = azurerm_storage_account.aml.id, subresource = "blob", zones = ["blob"] }
    keyvault       = { resource_id = azurerm_key_vault.main.id, subresource = "vault", zones = ["vault"] }
    acr            = { resource_id = azurerm_container_registry.main.id, subresource = "registry", zones = ["acr"] }
    redis          = { resource_id = azurerm_redis_cache.feast_online.id, subresource = "redisCache", zones = ["redis"] }
    eventhub       = { resource_id = azurerm_eventhub_namespace.main.id, subresource = "namespace", zones = ["eventhub"] }
    aml-workspace  = { resource_id = azurerm_machine_learning_workspace.main.id, subresource = "amlworkspace", zones = ["aml_api", "aml_nb"] }
    databricks-api = { resource_id = azurerm_databricks_workspace.main.id, subresource = "databricks_ui_api", zones = ["databricks"] }
    adf            = { resource_id = azurerm_data_factory.main.id, subresource = "dataFactory", zones = ["adf"] }
    purview        = { resource_id = azurerm_purview_account.main.id, subresource = "account", zones = ["purview"] }
    purview-portal = { resource_id = azurerm_purview_account.main.id, subresource = "portal", zones = ["purview_ui"] }
  }
}

resource "azurerm_private_endpoint" "this" {
  for_each            = local.private_endpoints
  name                = "pe-${each.key}-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.spoke["snet-private-endpoints"].id

  private_service_connection {
    name                           = "psc-${each.key}"
    private_connection_resource_id = each.value.resource_id
    subresource_names              = [each.value.subresource]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-${each.key}"
    private_dns_zone_ids = [for z in each.value.zones : azurerm_private_dns_zone.this[z].id]
  }

  tags = local.tags
}

# =========================================================================
# 13. AKS PRIVATE CLUSTER (KSERVE SERVING, WORKLOAD IDENTITY, 3 AZs)
# =========================================================================
resource "azurerm_role_assignment" "aks_network_contributor" {
  scope                = azurerm_virtual_network.spoke.id
  role_definition_name = "Network Contributor"
  principal_id         = azurerm_user_assigned_identity.aks.principal_id
}

resource "azurerm_role_assignment" "aks_route_table" {
  scope                = azurerm_route_table.spoke_egress.id
  role_definition_name = "Network Contributor"
  principal_id         = azurerm_user_assigned_identity.aks.principal_id
}

resource "azurerm_kubernetes_cluster" "main" {
  name                      = "aks-${local.name_prefix}"
  location                  = azurerm_resource_group.main.location
  resource_group_name       = azurerm_resource_group.main.name
  dns_prefix                = "aks-${local.name_prefix}"
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
    vnet_subnet_id               = azurerm_subnet.spoke["snet-aks-system"].id
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

    tags = local.tags
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aks.id]
  }

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

  # Azure Monitor managed Prometheus (scraped metrics -> Azure Monitor workspace)
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
    day_of_week = "Sunday"
    start_time  = "01:00"
    utc_offset  = "+00:00"
  }

  tags = local.tags

  depends_on = [
    azurerm_role_assignment.aks_network_contributor,
    azurerm_role_assignment.aks_route_table,
    azurerm_subnet_route_table_association.spoke,
    azurerm_firewall_policy_rule_collection_group.aks_egress,
  ]
}

resource "azurerm_kubernetes_cluster_node_pool" "inference" {
  name                  = "cpuinfer"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  mode                  = "User"
  vm_size               = var.aks_user_vm_size
  zones                 = var.availability_zones
  vnet_subnet_id        = azurerm_subnet.spoke["snet-aks-user"].id
  auto_scaling_enabled  = true
  min_count             = var.aks_user_node_count.min
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

  tags = local.tags
}

# =========================================================================
# 14. API MANAGEMENT (INTERNAL VNET MODE, ZONE-REDUNDANT)
# =========================================================================
resource "azurerm_public_ip" "apim" {
  name                = "pip-apim-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Static"
  sku                 = "Standard"
  zones               = var.availability_zones
  domain_name_label   = "apim-${local.name_prefix}-${random_string.suffix.result}"
  tags                = local.tags
}

resource "azurerm_api_management" "main" {
  name                 = "apim-${local.name_prefix}-${random_string.suffix.result}"
  location             = azurerm_resource_group.main.location
  resource_group_name  = azurerm_resource_group.main.name
  publisher_name       = var.apim_publisher_name
  publisher_email      = var.apim_publisher_email
  sku_name             = var.apim_sku
  zones                = var.apim_zones # one Premium unit per zone (Premium_2 -> AZ1 + AZ2)
  virtual_network_type = "Internal"
  public_ip_address_id = azurerm_public_ip.apim.id
  min_api_version      = "2021-08-01"

  virtual_network_configuration {
    subnet_id = azurerm_subnet.spoke["snet-apim"].id
  }

  # DR: APIM regional gateway unit in North Europe (internal VNet mode in the DR spoke)
  dynamic "additional_location" {
    for_each = var.enable_dr ? [var.dr_location] : []
    content {
      location             = additional_location.value
      capacity             = var.apim_dr_capacity
      public_ip_address_id = azurerm_public_ip.apim_dr[0].id

      virtual_network_configuration {
        subnet_id = azurerm_subnet.dr["snet-apim"].id
      }
    }
  }

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags

  depends_on = [
    azurerm_subnet_network_security_group_association.spoke,
    azurerm_subnet_network_security_group_association.dr,
  ]
}

# =========================================================================
# 14b. APPLICATION GATEWAY (PRIVATE INGRESS FOR FRONT DOOR -> INTERNAL APIM)
# Front Door cannot reach internal-mode APIM directly. Each region gets a
# Standard_v2 App Gateway with a private frontend (listener) exposed to Front
# Door Premium through App Gateway Private Link; the backend is the APIM
# internal gateway private IP. WAF is enforced at the Front Door edge.
# =========================================================================
locals {
  apim_gateway_host_name = trimprefix(azurerm_api_management.main.gateway_url, "https://")

  # The Front Door private_link `target_type` (Private Link group ID) for an App
  # Gateway origin is the name of the frontend IP configuration bound to the
  # Private Link configuration. azurerm 4.x only accepts a fixed list of
  # target_type values, so the private frontend is deliberately named "Gateway".
  appgw_private_frontend_name = "Gateway"
  appgw_private_link_name     = "plc-afd"

  api_ingress_regions_all = {
    primary = {
      name                = "agw-${local.name_prefix}"
      location            = azurerm_resource_group.main.location
      resource_group_name = azurerm_resource_group.main.name
      appgw_subnet_id     = azurerm_subnet.spoke["snet-appgw"].id
      pl_subnet_id        = azurerm_subnet.spoke["snet-appgw-pl"].id
      private_ip          = cidrhost(var.spoke_subnets["snet-appgw"].cidr, 10)
      apim_private_ips    = azurerm_api_management.main.private_ip_addresses
      afd_priority        = 1
    }
    dr = {
      name                = "agw-${local.name_prefix}-dr"
      location            = azurerm_resource_group.dr.location
      resource_group_name = azurerm_resource_group.dr.name
      appgw_subnet_id     = azurerm_subnet.dr["snet-appgw"].id
      pl_subnet_id        = azurerm_subnet.dr["snet-appgw-pl"].id
      private_ip          = cidrhost(var.dr_spoke_subnets["snet-appgw"].cidr, 10)
      apim_private_ips    = try(azurerm_api_management.main.additional_location[0].private_ip_addresses, [])
      afd_priority        = 2
    }
  }

  api_ingress_regions = { for k, v in local.api_ingress_regions_all : k => v if k == "primary" || var.enable_dr }
}

resource "azurerm_user_assigned_identity" "appgw" {
  name                = "id-appgw-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

# Listener certificate is read from Key Vault (through its private endpoint)
resource "azurerm_role_assignment" "appgw_kv_secrets" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.appgw.principal_id
}

# App Gateway v2 still requires a public frontend for its control plane; no
# listener is bound to it and the subnet NSG denies Internet inbound.
resource "azurerm_public_ip" "appgw" {
  for_each            = local.api_ingress_regions
  name                = "pip-${each.value.name}"
  location            = each.value.location
  resource_group_name = each.value.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  zones               = var.availability_zones
  tags                = local.tags
}

resource "azurerm_application_gateway" "api" {
  for_each            = local.api_ingress_regions
  name                = each.value.name
  location            = each.value.location
  resource_group_name = each.value.resource_group_name
  zones               = var.availability_zones

  sku {
    name = "Standard_v2"
    tier = "Standard_v2"
  }

  autoscale_configuration {
    min_capacity = var.appgw_autoscale.min
    max_capacity = var.appgw_autoscale.max
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.appgw.id]
  }

  gateway_ip_configuration {
    name      = "gwipc"
    subnet_id = each.value.appgw_subnet_id
  }

  frontend_ip_configuration {
    name                 = "fe-public"
    public_ip_address_id = azurerm_public_ip.appgw[each.key].id
  }

  frontend_ip_configuration {
    name                            = local.appgw_private_frontend_name
    subnet_id                       = each.value.appgw_subnet_id
    private_ip_address              = each.value.private_ip
    private_ip_address_allocation   = "Static"
    private_link_configuration_name = local.appgw_private_link_name
  }

  # Private Link NAT IPs live in a dedicated subnet (cannot be the gateway subnet)
  private_link_configuration {
    name = local.appgw_private_link_name

    ip_configuration {
      name                          = "plc-ipconfig"
      subnet_id                     = each.value.pl_subnet_id
      private_ip_address_allocation = "Dynamic"
      primary                       = true
    }
  }

  frontend_port {
    name = "https-443"
    port = 443
  }

  ssl_certificate {
    name                = "api-origin-cert"
    key_vault_secret_id = var.appgw_ssl_certificate_secret_id
  }

  ssl_policy {
    policy_type = "Predefined"
    policy_name = "AppGwSslPolicy20220101"
  }

  http_listener {
    name                           = "listener-api-private"
    frontend_ip_configuration_name = local.appgw_private_frontend_name
    frontend_port_name             = "https-443"
    protocol                       = "Https"
    ssl_certificate_name           = "api-origin-cert"
  }

  # Internal APIM gateway private IP(s); host header overridden to the APIM
  # default host so its *.azure-api.net certificate validates.
  backend_address_pool {
    name         = "pool-apim-internal"
    ip_addresses = each.value.apim_private_ips
  }

  probe {
    name                                      = "probe-apim-status"
    protocol                                  = "Https"
    host                                      = local.apim_gateway_host_name
    path                                      = "/status-0123456789abcdef"
    interval                                  = 30
    timeout                                   = 30
    unhealthy_threshold                       = 3
    pick_host_name_from_backend_http_settings = false

    match {
      status_code = ["200-399"]
    }
  }

  backend_http_settings {
    name                                = "https-apim"
    cookie_based_affinity               = "Disabled"
    port                                = 443
    protocol                            = "Https"
    request_timeout                     = 30
    host_name                           = local.apim_gateway_host_name
    pick_host_name_from_backend_address = false
    probe_name                          = "probe-apim-status"
  }

  request_routing_rule {
    name                       = "rule-api-to-apim"
    priority                   = 100
    rule_type                  = "Basic"
    http_listener_name         = "listener-api-private"
    backend_address_pool_name  = "pool-apim-internal"
    backend_http_settings_name = "https-apim"
  }

  tags = local.tags

  depends_on = [
    azurerm_role_assignment.appgw_kv_secrets,
    azurerm_subnet_network_security_group_association.spoke,
    azurerm_subnet_network_security_group_association.dr,
    azurerm_private_endpoint.this,
    azurerm_private_endpoint.dr, # DR gateway reads its certificate via the DR Key Vault endpoint
  ]
}

# =========================================================================
# 15. AZURE FRONT DOOR PREMIUM + WAF POLICY
# =========================================================================
resource "azurerm_cdn_frontdoor_profile" "main" {
  name                     = "afd-${local.name_prefix}"
  resource_group_name      = azurerm_resource_group.main.name
  sku_name                 = "Premium_AzureFrontDoor"
  response_timeout_seconds = 30
  tags                     = local.tags
}

resource "azurerm_cdn_frontdoor_firewall_policy" "main" {
  name                              = "waf${var.project}${var.environment}"
  resource_group_name               = azurerm_resource_group.main.name
  sku_name                          = azurerm_cdn_frontdoor_profile.main.sku_name
  enabled                           = true
  mode                              = "Prevention"
  custom_block_response_status_code = 403

  custom_rule {
    name                           = "RateLimitPerClientIP"
    enabled                        = true
    priority                       = 1
    type                           = "RateLimitRule"
    action                         = "Block"
    rate_limit_duration_in_minutes = 1
    rate_limit_threshold           = var.waf_rate_limit_per_minute

    match_condition {
      match_variable     = "RemoteAddr"
      operator           = "IPMatch"
      negation_condition = true
      match_values       = ["127.0.0.1"]
    }
  }

  managed_rule {
    type    = "Microsoft_DefaultRuleSet"
    version = "2.1"
    action  = "Block"
  }

  managed_rule {
    type    = "Microsoft_BotManagerRuleSet"
    version = "1.1"
    action  = "Block"
  }

  tags = local.tags
}

resource "azurerm_cdn_frontdoor_endpoint" "api" {
  name                     = "fde-${local.name_prefix}-${random_string.suffix.result}"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.main.id
  tags                     = local.tags
}

resource "azurerm_cdn_frontdoor_origin_group" "apim" {
  name                     = "og-apim"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.main.id
  session_affinity_enabled = false

  load_balancing {
    sample_size                 = 4
    successful_samples_required = 3
  }

  health_probe {
    path                = "/status-0123456789abcdef"
    protocol            = "Https"
    request_type        = "GET"
    interval_in_seconds = 30
  }
}

# Front Door Premium -> App Gateway private frontend over Private Link, one
# origin per region (priority 1 = West Europe, 2 = North Europe warm standby).
#
# POST-APPLY STEP: each origin creates a *pending* private endpoint connection
# on its App Gateway. Approve it once after the first apply with
# scripts/post-apply.sh (see POST_APPLY.md); until approved, Front Door health
# probes fail and the route returns 5xx.
resource "azurerm_cdn_frontdoor_origin" "apim" {
  for_each                       = local.api_ingress_regions
  name                           = "origin-appgw-${each.key}"
  cdn_frontdoor_origin_group_id  = azurerm_cdn_frontdoor_origin_group.apim.id
  enabled                        = true
  host_name                      = each.value.private_ip
  origin_host_header             = var.api_origin_host_name
  certificate_name_check_enabled = true
  http_port                      = 80
  https_port                     = 443
  priority                       = each.value.afd_priority
  weight                         = 1000

  private_link {
    request_message        = "Front Door private origin for churn scoring API (${each.key})" # matched by scripts/post-apply.sh
    target_type            = local.appgw_private_frontend_name
    location               = each.value.location
    private_link_target_id = azurerm_application_gateway.api[each.key].id
  }
}

resource "azurerm_cdn_frontdoor_route" "api" {
  name                          = "route-churn-api"
  cdn_frontdoor_endpoint_id     = azurerm_cdn_frontdoor_endpoint.api.id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.apim.id
  cdn_frontdoor_origin_ids      = [for o in azurerm_cdn_frontdoor_origin.apim : o.id]
  enabled                       = true
  forwarding_protocol           = "HttpsOnly"
  https_redirect_enabled        = true
  patterns_to_match             = ["/churn/*"]
  supported_protocols           = ["Http", "Https"]
  link_to_default_domain        = true
}

resource "azurerm_cdn_frontdoor_security_policy" "waf" {
  name                     = "secpol-churn-api"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.main.id

  security_policies {
    firewall {
      cdn_frontdoor_firewall_policy_id = azurerm_cdn_frontdoor_firewall_policy.main.id

      association {
        patterns_to_match = ["/*"]
        domain {
          cdn_frontdoor_domain_id = azurerm_cdn_frontdoor_endpoint.api.id
        }
      }
    }
  }
}

# =========================================================================
# 16. ROLE ASSIGNMENTS (LEAST PRIVILEGE VIA MANAGED IDENTITIES)
# =========================================================================
locals {
  role_assignments = {
    aks-kubelet-acrpull = {
      scope     = azurerm_container_registry.main.id
      role      = "AcrPull"
      principal = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
    }
    serving-lake-reader = {
      scope     = azurerm_storage_account.lake.id
      role      = "Storage Blob Data Reader"
      principal = azurerm_user_assigned_identity.serving.principal_id
    }
    serving-kv-secrets = {
      scope     = azurerm_key_vault.main.id
      role      = "Key Vault Secrets User"
      principal = azurerm_user_assigned_identity.serving.principal_id
    }
    serving-eventhub-sender = {
      scope     = azurerm_eventhub.this["churn-score-feed"].id
      role      = "Azure Event Hubs Data Sender"
      principal = azurerm_user_assigned_identity.serving.principal_id
    }
    aml-lake-contributor = {
      scope     = azurerm_storage_account.lake.id
      role      = "Storage Blob Data Contributor"
      principal = azurerm_user_assigned_identity.aml.principal_id
    }
    aml-store-contributor = {
      scope     = azurerm_storage_account.aml.id
      role      = "Storage Blob Data Contributor"
      principal = azurerm_user_assigned_identity.aml.principal_id
    }
    aml-acr-push = {
      scope     = azurerm_container_registry.main.id
      role      = "AcrPush"
      principal = azurerm_user_assigned_identity.aml.principal_id
    }
    aml-kv-secrets = {
      scope     = azurerm_key_vault.main.id
      role      = "Key Vault Secrets Officer"
      principal = azurerm_user_assigned_identity.aml.principal_id
    }
    databricks-lake-contributor = {
      scope     = azurerm_storage_account.lake.id
      role      = "Storage Blob Data Contributor"
      principal = azurerm_databricks_access_connector.main.identity[0].principal_id
    }
    databricks-eventhub-receiver = {
      scope     = azurerm_eventhub_namespace.main.id
      role      = "Azure Event Hubs Data Receiver"
      principal = azurerm_databricks_access_connector.main.identity[0].principal_id
    }
    adf-lake-contributor = {
      scope     = azurerm_storage_account.lake.id
      role      = "Storage Blob Data Contributor"
      principal = azurerm_data_factory.main.identity[0].principal_id
    }
    apim-kv-secrets = {
      scope     = azurerm_key_vault.main.id
      role      = "Key Vault Secrets User"
      principal = azurerm_api_management.main.identity[0].principal_id
    }
    grafana-monitor-reader = {
      scope     = azurerm_resource_group.main.id
      role      = "Monitoring Reader"
      principal = azurerm_dashboard_grafana.main.identity[0].principal_id
    }
    grafana-prometheus-reader = {
      scope     = azurerm_monitor_workspace.prometheus.id
      role      = "Monitoring Data Reader"
      principal = azurerm_dashboard_grafana.main.identity[0].principal_id
    }
  }
}

# AML workspace identity needs control-plane rights on its resource group
resource "azurerm_role_assignment" "aml_rg_contributor" {
  scope                = azurerm_resource_group.main.id
  role_definition_name = "Contributor"
  principal_id         = azurerm_user_assigned_identity.aml.principal_id
}

resource "azurerm_role_assignment" "this" {
  for_each             = local.role_assignments
  scope                = each.value.scope
  role_definition_name = each.value.role
  principal_id         = each.value.principal
}

# Redis data access for KServe Transformer (Feast online lookups) via Entra ID
resource "azurerm_redis_cache_access_policy_assignment" "serving" {
  name               = "serving-feast-reader"
  redis_cache_id     = azurerm_redis_cache.feast_online.id
  access_policy_name = "Data Reader"
  object_id          = azurerm_user_assigned_identity.serving.principal_id
  object_id_alias    = "id-serving"
}

resource "azurerm_redis_cache_access_policy_assignment" "batch_writer" {
  name               = "aml-feast-writer"
  redis_cache_id     = azurerm_redis_cache.feast_online.id
  access_policy_name = "Data Contributor"
  object_id          = azurerm_user_assigned_identity.aml.principal_id
  object_id_alias    = "id-aml"
}

# =========================================================================
# 17. SECURITY POSTURE & AUDIT LOGGING
# =========================================================================
resource "azurerm_security_center_subscription_pricing" "defender" {
  for_each      = var.enable_defender ? toset(["Containers", "KeyVaults", "StorageAccounts", "Arm", "VirtualMachines"]) : toset([])
  tier          = "Standard"
  resource_type = each.value
}

locals {
  appgw_diagnostic_targets = {
    for k in keys(local.api_ingress_regions) :
    "appgw-${k}" => { id = azurerm_application_gateway.api[k].id, categories = ["ApplicationGatewayAccessLog"] }
  }

  diagnostic_targets_base = {
    aks       = { id = azurerm_kubernetes_cluster.main.id, categories = ["kube-audit-admin", "kube-apiserver", "guard"] }
    keyvault  = { id = azurerm_key_vault.main.id, categories = ["AuditEvent"] }
    apim      = { id = azurerm_api_management.main.id, categories = ["GatewayLogs"] }
    firewall  = { id = azurerm_firewall.hub.id, categories = ["AZFWApplicationRule", "AZFWNetworkRule", "AZFWThreatIntel"] }
    frontdoor = { id = azurerm_cdn_frontdoor_profile.main.id, categories = ["FrontDoorAccessLog", "FrontDoorWebApplicationFirewallLog"] }
    aml       = { id = azurerm_machine_learning_workspace.main.id, categories = ["AmlComputeJobEvent", "ModelsChangeEvent"] }
  }

  diagnostic_targets = merge(local.diagnostic_targets_base, local.appgw_diagnostic_targets)
}

resource "azurerm_monitor_diagnostic_setting" "this" {
  for_each                       = local.diagnostic_targets
  name                           = "diag-${each.key}-to-law"
  target_resource_id             = each.value.id
  log_analytics_workspace_id     = azurerm_log_analytics_workspace.main.id
  log_analytics_destination_type = "Dedicated"

  dynamic "enabled_log" {
    for_each = toset(each.value.categories)
    content {
      category = enabled_log.value
    }
  }
}

# =========================================================================
# 18. FINOPS: CONSUMPTION BUDGET (USD 600K / YEAR)
# =========================================================================
resource "azurerm_consumption_budget_resource_group" "main" {
  name              = "budget-${local.name_prefix}"
  resource_group_id = azurerm_resource_group.main.id
  amount            = var.monthly_budget_usd
  time_grain        = "Monthly"

  time_period {
    start_date = var.budget_start_date
  }

  notification {
    enabled        = true
    threshold      = 80
    operator       = "GreaterThanOrEqualTo"
    threshold_type = "Actual"
    contact_emails = var.budget_alert_emails
  }

  notification {
    enabled        = true
    threshold      = 100
    operator       = "GreaterThanOrEqualTo"
    threshold_type = "Forecasted"
    contact_emails = var.budget_alert_emails
  }

  notification {
    enabled        = true
    threshold      = 110
    operator       = "GreaterThanOrEqualTo"
    threshold_type = "Actual"
    contact_emails = var.budget_alert_emails
  }
}
