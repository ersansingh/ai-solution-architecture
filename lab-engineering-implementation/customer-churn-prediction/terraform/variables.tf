# =========================================================================
# CUSTOMER CHURN PREDICTION PLATFORM - INPUT VARIABLES
# =========================================================================

# -------------------------------------------------------------------------
# Subscription, naming & placement
# -------------------------------------------------------------------------
variable "subscription_id" {
  description = "Azure subscription ID hosting the churn platform spoke and hub."
  type        = string
}

variable "project" {
  description = "Short project code used in resource names (lowercase, alphanumeric)."
  type        = string
  default     = "churn"

  validation {
    condition     = can(regex("^[a-z0-9]{3,8}$", var.project))
    error_message = "project must be 3-8 lowercase alphanumeric characters."
  }
}

variable "environment" {
  description = "Deployment environment (dev, stg, prod)."
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "stg", "prod"], var.environment)
    error_message = "environment must be one of dev, stg, prod."
  }
}

variable "location" {
  description = "Primary Azure region (3 availability zones)."
  type        = string
  default     = "westeurope"
}

variable "dr_location" {
  description = "Disaster recovery region (warm standby, active-passive)."
  type        = string
  default     = "northeurope"
}

variable "enable_dr" {
  description = "Deploy the costly North Europe warm-standby components (DR AKS at minimum scale with managed Prometheus, Redis geo-replica, DR-region private endpoints, APIM regional unit, DR Application Gateway + Front Door priority-2 origin). The DR resource group, VNet, subnets, NSGs, DR privatelink DNS zones and peering are always deployed. Requires dr_hub_vnet_id and dr_hub_firewall_private_ip (DR egress is forced through the North Europe hub firewall)."
  type        = bool
  default     = true
}

variable "availability_zones" {
  description = "Availability zones used for zone-redundant resources."
  type        = list(string)
  default     = ["1", "2", "3"]
}

variable "tags" {
  description = "Additional tags merged onto every resource."
  type        = map(string)
  default = {
    CostCenter         = "CX-Analytics"
    Owner              = "ml-platform-team"
    DataClassification = "Confidential-PII"
    Compliance         = "GDPR-ISO27001-SOC2"
  }
}

# -------------------------------------------------------------------------
# Networking (hub-spoke)
# -------------------------------------------------------------------------
variable "hub_vnet_cidr" {
  description = "Address space of the hub VNet (Firewall, Bastion, VPN/ExpressRoute gateway)."
  type        = string
  default     = "10.10.0.0/16"
}

variable "hub_subnets" {
  description = "Hub subnets. Names are fixed by Azure for Firewall, Bastion and Gateway."
  type        = map(string)
  default = {
    AzureFirewallSubnet = "10.10.0.0/26"
    AzureBastionSubnet  = "10.10.1.0/26"
    GatewaySubnet       = "10.10.2.0/27"
  }
}

variable "spoke_vnet_cidr" {
  description = "Address space of the churn workload spoke VNet."
  type        = string
  default     = "10.20.0.0/16"
}

variable "spoke_subnets" {
  description = "Spoke subnets for AKS, APIM, private endpoints, Databricks (VNet injection) and Azure ML."
  type = map(object({
    cidr       = string
    delegation = optional(string)
    udr        = optional(bool, false)
  }))
  default = {
    snet-aks-system         = { cidr = "10.20.0.0/22", udr = true }
    snet-aks-user           = { cidr = "10.20.4.0/22", udr = true }
    snet-apim               = { cidr = "10.20.12.0/26" }
    snet-private-endpoints  = { cidr = "10.20.13.0/24" }
    snet-appgw              = { cidr = "10.20.14.0/24" } # Application Gateway v2 (API ingress in front of internal APIM)
    snet-appgw-pl           = { cidr = "10.20.15.0/27" } # App Gateway Private Link NAT IPs (Front Door origin); must not host gateways
    snet-databricks-public  = { cidr = "10.20.16.0/22", delegation = "Microsoft.Databricks/workspaces" }
    snet-databricks-private = { cidr = "10.20.20.0/22", delegation = "Microsoft.Databricks/workspaces" }
    snet-aml                = { cidr = "10.20.24.0/23" }
  }
}

variable "dr_spoke_vnet_cidr" {
  description = "Address space of the North Europe DR spoke VNet."
  type        = string
  default     = "10.30.0.0/16"
}

variable "dr_spoke_subnets" {
  description = "DR spoke subnets (mirror of the serving-path subnets in the primary spoke; Databricks/AML are redeployed from IaC on regional failover)."
  type = map(object({
    cidr       = string
    delegation = optional(string)
    udr        = optional(bool, false)
  }))
  default = {
    snet-aks-system        = { cidr = "10.30.0.0/22", udr = true }
    snet-aks-user          = { cidr = "10.30.4.0/22", udr = true }
    snet-apim              = { cidr = "10.30.12.0/26" }
    snet-private-endpoints = { cidr = "10.30.13.0/24" }
    snet-appgw             = { cidr = "10.30.14.0/24" }
    snet-appgw-pl          = { cidr = "10.30.15.0/27" }
  }
}

variable "dr_hub_vnet_id" {
  description = "ID of the platform-owned North Europe hub VNet to peer the DR spoke with (the hub-side peering is created by the platform team). Required when enable_dr = true; null skips the peering."
  type        = string
  default     = null
}

variable "dr_hub_firewall_private_ip" {
  description = "Private IP of the North Europe hub Azure Firewall. DR AKS subnets get a 0.0.0.0/0 UDR to it and the DR cluster uses userDefinedRouting egress. Required when enable_dr = true: there is no load-balancer public-IP fallback (Azure Policy denies public IPs)."
  type        = string
  default     = null

  validation {
    condition     = var.dr_hub_firewall_private_ip == null || can(cidrhost("${coalesce(var.dr_hub_firewall_private_ip, "0.0.0.0")}/32", 0))
    error_message = "dr_hub_firewall_private_ip must be an IPv4 address (or null when enable_dr = false)."
  }
}

variable "enable_vpn_gateway" {
  description = "Deploy a zone-redundant VPN gateway in the hub for on-prem CRM/Billing connectivity (use ExpressRoute in production if available)."
  type        = bool
  default     = false
}

variable "deployer_allowed_ips" {
  description = "Public CIDRs of CI runners/operators allowed through Key Vault firewall during bootstrap (prefer self-hosted runners inside the VNet)."
  type        = list(string)
  default     = []
}

# -------------------------------------------------------------------------
# AKS (KServe real-time serving)
# -------------------------------------------------------------------------
variable "kubernetes_version" {
  description = "AKS Kubernetes minor version (1.35 is GA on AKS until ~Mar 2027). AKS supports only ~3 minor versions at a time: before applying, confirm the version is still supported in both regions with `az aks get-versions --location westeurope -o table` (and northeurope), and bump it as versions reach end of life."
  type        = string
  default     = "1.35"

  validation {
    condition     = can(regex("^1\\.(3[4-9]|[4-9][0-9])(\\.[0-9]+)?$", var.kubernetes_version))
    error_message = "kubernetes_version must be 1.34 or newer (format 1.MM or 1.MM.P); 1.33 and older are out of AKS standard support. Check `az aks get-versions --location <region> -o table` for currently supported versions."
  }
}

variable "aks_system_vm_size" {
  description = "VM size for the AKS system node pool."
  type        = string
  default     = "Standard_D4s_v5"
}

variable "aks_system_node_count" {
  description = "Min/max node counts for the system pool."
  type        = object({ min = number, max = number })
  default     = { min = 3, max = 6 }
}

variable "aks_user_vm_size" {
  description = "VM size for the CPU inference user node pool (KServe Transformer/Predictor/Explainer)."
  type        = string
  default     = "Standard_D8s_v5"
}

variable "aks_user_node_count" {
  description = "Min/max node counts for the user pool (sized for 5,000 RPS peak with HPA)."
  type        = object({ min = number, max = number })
  default     = { min = 4, max = 16 }
}

variable "aks_service_cidr" {
  description = "Kubernetes service CIDR (must not overlap VNets)."
  type        = string
  default     = "172.16.0.0/16"
}

variable "aks_dns_service_ip" {
  description = "Kubernetes DNS service IP inside the service CIDR."
  type        = string
  default     = "172.16.0.10"
}

variable "aks_pod_cidr" {
  description = "Pod CIDR for Azure CNI Overlay."
  type        = string
  default     = "192.168.0.0/16"
}

variable "aks_admin_group_object_ids" {
  description = "Entra ID group object IDs granted AKS cluster admin (via PIM)."
  type        = list(string)
  default     = []
}

variable "kserve_namespace" {
  description = "Kubernetes namespace hosting the churn KServe InferenceService."
  type        = string
  default     = "churn-serving"
}

variable "kserve_service_account" {
  description = "Kubernetes service account federated to the serving workload identity."
  type        = string
  default     = "churn-kserve-sa"
}

# -------------------------------------------------------------------------
# Azure ML training compute
# -------------------------------------------------------------------------
variable "aml_training_vm_size" {
  description = "CPU VM size for LightGBM/CatBoost training."
  type        = string
  default     = "Standard_F32s_v2"
}

variable "aml_training_max_nodes" {
  description = "Max nodes for the dedicated training cluster."
  type        = number
  default     = 8
}

variable "aml_tuning_vm_size" {
  description = "CPU VM size for Optuna hyperparameter tuning sweeps."
  type        = string
  default     = "Standard_F16s_v2"
}

variable "aml_tuning_max_nodes" {
  description = "Max nodes for the tuning cluster."
  type        = number
  default     = 20
}

variable "aml_tuning_low_priority" {
  description = "Use low-priority (spot) VMs for the tuning cluster (FinOps)."
  type        = bool
  default     = true
}

variable "aml_batch_vm_size" {
  description = "CPU VM size for the daily batch scoring of 18M customers (parallel run step + TreeSHAP)."
  type        = string
  default     = "Standard_D16s_v5"
}

variable "aml_batch_max_nodes" {
  description = "Max nodes for the dedicated batch scoring cluster (scales to zero when idle)."
  type        = number
  default     = 10
}

# -------------------------------------------------------------------------
# Data platform
# -------------------------------------------------------------------------
variable "lake_containers" {
  description = "ADLS Gen2 filesystems for the Delta medallion lake and Feast offline store."
  type        = list(string)
  default     = ["bronze", "silver", "gold", "feast-offline", "audit"]
}

variable "event_hubs" {
  description = "Event Hubs for streaming churn signals."
  type = map(object({
    partitions     = number
    retention_days = number
  }))
  default = {
    support-calls    = { partitions = 8, retention_days = 7 }
    app-sessions     = { partitions = 16, retention_days = 7 }
    payments         = { partitions = 8, retention_days = 7 }
    churn-score-feed = { partitions = 8, retention_days = 3 }
  }
}

variable "enable_stream_analytics_cluster" {
  description = "Deploy a dedicated Stream Analytics cluster (36 SU minimum) with managed private endpoints to the private-only Event Hubs namespace and ADLS. Required for the ASA job to start, because both are public-network-disabled; costly, so off by default (Databricks Structured Streaming then computes the windowed features)."
  type        = bool
  default     = false
}

variable "stream_analytics_streaming_units" {
  description = "Streaming units for the windowed streaming-features ASA job."
  type        = number
  default     = 3
}

variable "stream_analytics_output_container" {
  description = "Lake filesystem receiving the ASA windowed features (path streaming-features/{date}/{time}) for the Feast push/materialization job."
  type        = string
  default     = "silver"
}

variable "eventhub_capacity" {
  description = "Event Hubs Standard throughput units."
  type        = number
  default     = 4
}

variable "redis_capacity" {
  description = "Azure Cache for Redis Premium size (P1-P5). 18M customers x score+drivers ~ P3."
  type        = number
  default     = 3
}

variable "redis_shard_count" {
  description = "Number of Redis cluster shards."
  type        = number
  default     = 2
}

variable "redis_aof_persistence_enabled" {
  description = "Request AOF persistence (managed-identity auth, dedicated storage account) on the Feast online store. Azure does not support persistence on geo-replicated caches, so it only takes effect when enable_dr = false; with DR on, the geo-replica plus rebuild from Gold churn_scores provide durability."
  type        = bool
  default     = true
}

# -------------------------------------------------------------------------
# API edge
# -------------------------------------------------------------------------
variable "apim_sku" {
  description = "API Management SKU and unit count (Premium required for internal VNet mode with zones). The unit count must be a multiple of the number of apim_zones."
  type        = string
  default     = "Premium_2"
}

variable "apim_zones" {
  description = "Availability zones for the primary APIM units (2 zone-redundant units: AZ1 + AZ2)."
  type        = list(string)
  default     = ["1", "2"]
}

variable "apim_publisher_name" {
  description = "APIM publisher name."
  type        = string
  default     = "Churn Platform Team"
}

variable "apim_publisher_email" {
  description = "APIM publisher email."
  type        = string
  default     = "ml-platform@example.com"
}

variable "apim_dr_capacity" {
  description = "APIM Premium units in the DR region (additional_location), used when enable_dr is true."
  type        = number
  default     = 1
}

variable "api_origin_host_name" {
  description = "API host name sent by Front Door as the origin Host header and served by the Application Gateway HTTPS listener. Must match the certificate in appgw_ssl_certificate_secret_id."
  type        = string
  default     = "api-internal.churn.example.com"
}

variable "appgw_ssl_certificate_secret_id" {
  description = "Key Vault secret ID (versionless preferred) of a publicly trusted PFX certificate for api_origin_host_name, used by the Application Gateway listener (Front Door requires a CA-trusted origin certificate)."
  type        = string
}

variable "appgw_autoscale" {
  description = "Min/max autoscale instances for the API Application Gateway (Standard_v2), per region."
  type        = object({ min = number, max = number })
  default     = { min = 2, max = 10 }
}

variable "waf_rate_limit_per_minute" {
  description = "Per-client-IP request limit enforced by the Front Door WAF."
  type        = number
  default     = 6000
}

# -------------------------------------------------------------------------
# Observability, security & FinOps
# -------------------------------------------------------------------------
variable "log_retention_days" {
  description = "Log Analytics retention in days."
  type        = number
  default     = 90
}

variable "enable_defender" {
  description = "Enable Microsoft Defender for Cloud plans on the subscription."
  type        = bool
  default     = true
}

variable "monthly_budget_usd" {
  description = "Monthly consumption budget (USD 600K/yr = 50K/month)."
  type        = number
  default     = 50000
}

variable "budget_start_date" {
  description = "Budget start date (first day of a month, RFC3339)."
  type        = string
  default     = "2026-11-01T00:00:00Z"
}

variable "budget_alert_emails" {
  description = "Recipients of budget threshold alerts."
  type        = list(string)
  default     = ["finops@example.com", "ml-platform@example.com"]
}
