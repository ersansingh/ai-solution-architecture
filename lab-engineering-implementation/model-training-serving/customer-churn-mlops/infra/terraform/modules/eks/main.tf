data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.31"

  cluster_name                             = var.cluster_name
  cluster_version                          = var.cluster_version
  cluster_endpoint_public_access           = var.endpoint_public_access
  cluster_endpoint_public_access_cidrs     = var.endpoint_public_access_cidrs
  enable_cluster_creator_admin_permissions = true
  enable_irsa                              = true

  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnet_ids

  cluster_addons = {
    coredns                = {}
    kube-proxy             = {}
    vpc-cni                = { before_compute = true }
    eks-pod-identity-agent = {}
  }

  # >= 2 nodes spread over 3 AZs: churn-api pods are spread by topologySpreadConstraints (R6, 99.9%).
  eks_managed_node_groups = {
    default = {
      instance_types = var.node_instance_types
      min_size       = var.node_min
      max_size       = var.node_max
      desired_size   = var.node_desired
      subnet_ids     = var.private_subnet_ids
      labels         = { workload = "churn" }
    }
  }

  access_entries = {
    for name, arn in var.admin_role_arns : name => {
      principal_arn = arn
      policy_associations = {
        admin = {
          policy_arn   = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
          access_scope = { type = "cluster" }
        }
      }
    }
  }

  tags = var.tags
}

# ---- AWS Load Balancer Controller (binds churn-api pods to the Terraform-owned NLB target group) ----
module "lb_controller_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.48"

  role_name                              = "${var.cluster_name}-lb-controller"
  attach_load_balancer_controller_policy = true
  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:aws-load-balancer-controller"]
    }
  }
  tags = var.tags
}

resource "helm_release" "lb_controller" {
  name       = "aws-load-balancer-controller"
  namespace  = "kube-system"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  version    = var.lb_controller_chart_version

  values = [yamlencode({
    clusterName = module.eks.cluster_name
    region      = data.aws_region.current.name
    vpcId       = var.vpc_id
    serviceAccount = {
      name        = "aws-load-balancer-controller"
      annotations = { "eks.amazonaws.com/role-arn" = module.lb_controller_irsa.iam_role_arn }
    }
  })]

  depends_on = [module.eks]
}

resource "helm_release" "metrics_server" {
  name       = "metrics-server"
  namespace  = "kube-system"
  repository = "https://kubernetes-sigs.github.io/metrics-server/"
  chart      = "metrics-server"
  version    = var.metrics_server_chart_version
  depends_on = [module.eks]
}

resource "kubernetes_namespace" "churn" {
  metadata {
    name   = var.app_namespace
    labels = { project = "teleconnect-churn" }
  }
  depends_on = [module.eks]
}

# ---- churn-api IRSA: least privilege for the request path ----
data "aws_iam_policy_document" "churn_api" {
  statement {
    sid       = "InvokeChurnEndpoints"
    actions   = ["sagemaker:InvokeEndpoint"]
    resources = ["arn:aws:sagemaker:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:endpoint/customer-churn-*"]
  }
  statement {
    sid       = "OnlineFeatures"
    actions   = ["sagemaker:GetRecord"]
    resources = [var.feature_group_arn]
  }
  statement {
    sid       = "ServingConfig"
    actions   = ["ssm:GetParameter"]
    resources = ["arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter${var.serving_config_parameter_prefix}*"]
  }
  statement {
    sid       = "Metrics"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "cloudwatch:namespace"
      values   = [var.metrics_namespace]
    }
  }
  statement {
    sid       = "DecryptOnlineStore"
    actions   = ["kms:Decrypt"]
    resources = [var.kms_key_arn]
  }
}

resource "aws_iam_policy" "churn_api" {
  name   = "${var.cluster_name}-churn-api"
  policy = data.aws_iam_policy_document.churn_api.json
}

module "churn_api_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.48"

  role_name        = "${var.cluster_name}-churn-api"
  role_policy_arns = { churn_api = aws_iam_policy.churn_api.arn }
  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["${var.app_namespace}:churn-api"]
    }
  }
  tags = var.tags
}
