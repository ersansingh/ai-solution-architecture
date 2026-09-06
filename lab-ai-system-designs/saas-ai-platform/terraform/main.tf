terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.50.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.13.0"
    }
  }
}

provider "aws" {
  region = var.primary_region
  default_tags {
    tags = {
      Project     = "Enterprise-SaaS-AI-Platform"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Tier        = "Mission-Critical"
    }
  }
}

# =========================================================================
# 1. NETWORKING: MULTI-AZ REGIONAL VPC FOR AI WORKLOADS
# =========================================================================
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.8.0"

  name = "${var.environment}-ai-platform-vpc"
  cidr = var.vpc_cidr

  azs              = ["${var.primary_region}a", "${var.primary_region}b", "${var.primary_region}c"]
  public_subnets   = [cidrsubnet(var.vpc_cidr, 4, 0), cidrsubnet(var.vpc_cidr, 4, 1), cidrsubnet(var.vpc_cidr, 4, 2)]
  private_subnets  = [cidrsubnet(var.vpc_cidr, 4, 3), cidrsubnet(var.vpc_cidr, 4, 4), cidrsubnet(var.vpc_cidr, 4, 5)]
  database_subnets = [cidrsubnet(var.vpc_cidr, 4, 6), cidrsubnet(var.vpc_cidr, 4, 7), cidrsubnet(var.vpc_cidr, 4, 8)]

  enable_nat_gateway   = true
  single_nat_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
    "karpenter.sh/discovery"          = "${var.environment}-ai-eks-cluster"
  }
}

# =========================================================================
# 2. AMAZON EKS CLUSTER WITH GPU & INFERENTIA NODE GROUPS
# =========================================================================
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.10.0"

  cluster_name    = "${var.environment}-ai-eks-cluster"
  cluster_version = "1.30"

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  enable_cluster_creator_admin_permissions = true

  eks_managed_node_groups = {
    # System & Ingress Controllers
    system = {
      min_size     = 3
      max_size     = 6
      desired_size = 3

      instance_types = ["m6i.xlarge"]
      capacity_type  = "ON_DEMAND"
    }

    # High-Performance NVIDIA L4 GPUs for vLLM Real-time Inference (Sub-150ms)
    gpu_inference_l4 = {
      min_size     = 3
      max_size     = 30
      desired_size = 6

      instance_types = ["g6.2xlarge", "g6.4xlarge"]
      capacity_type  = "ON_DEMAND"

      labels = {
        "workload"     = "vllm-inference"
        "accelerator"  = "nvidia-l4"
        "tier"         = "real-time"
      }

      taints = {
        dedicated = {
          key    = "ai.platform/gpu"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }
    }

    # 60% Spot Compute Pool for LoRA Fine-Tuning & Embeddings
    spot_training_pool = {
      min_size     = 0
      max_size     = 50
      desired_size = 4

      instance_types = ["trn1.2xlarge", "trn1.32xlarge", "p4d.24xlarge"]
      capacity_type  = "SPOT"

      labels = {
        "workload"    = "batch-training"
        "accelerator" = "trainium-spot"
      }

      taints = {
        dedicated = {
          key    = "ai.platform/spot-training"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }
    }
  }
}

# =========================================================================
# 3. OPENSEARCH SERVERLESS VECTOR DATABASE
# =========================================================================
resource "aws_opensearchserverless_collection" "vector_db" {
  name        = "${var.environment}-saas-vectors"
  type        = "VECTORSEARCH"
  description = "Multi-Tenant Vector Search Collection for Enterprise Copilots"
}

# =========================================================================
# 4. ELASTICACHE REDIS SEMANTIC CACHE (SUB-15ms RESPONSE)
# =========================================================================
resource "aws_elasticache_subnet_group" "cache_subnets" {
  name       = "${var.environment}-cache-subnets"
  subnet_ids = module.vpc.database_subnets
}

resource "aws_elasticache_replication_group" "semantic_cache" {
  replication_group_id = "${var.environment}-semantic-cache"
  description          = "Redis Semantic Prompt Cache for Cost Optimization"
  node_type            = "cache.r7g.large"
  port                 = 6379
  parameter_group_name = "default.redis7.cluster.on"
  subnet_group_name    = aws_elasticache_subnet_group.cache_subnets.name
  security_group_ids   = [aws_security_group.cache_sg.id]

  automatic_failover_enabled = true
  num_node_groups            = 3
  replicas_per_node_group    = 1
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}

resource "aws_security_group" "cache_sg" {
  name        = "${var.environment}-cache-sg"
  description = "Allow inbound Redis traffic from EKS pods"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# =========================================================================
# 5. AURORA POSTGRESQL GLOBAL DATABASE (ROW-LEVEL SECURITY & METADATA)
# =========================================================================
resource "aws_rds_global_cluster" "aurora_global" {
  global_cluster_identifier = "${var.environment}-aurora-global-ai"
  engine                    = "aurora-postgresql"
  engine_version            = "16.2"
  database_name             = "saas_ai_metadata"
  storage_encrypted         = true
}

module "aurora_primary" {
  source  = "terraform-aws-modules/rds-aurora/aws"
  version = "~> 9.3.0"

  name                  = "${var.environment}-aurora-primary"
  engine                = "aurora-postgresql"
  engine_version        = "16.2"
  global_cluster_identifier = aws_rds_global_cluster.aurora_global.id

  vpc_id                = module.vpc.vpc_id
  subnets               = module.vpc.database_subnets
  instance_class        = "db.r7g.xlarge"
  instances = {
    writer = {}
    reader = {}
  }

  storage_encrypted   = true
  apply_immediately   = true
  monitoring_interval = 10
}
