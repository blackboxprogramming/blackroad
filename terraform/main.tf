# BlackRoad AWS Infrastructure
# Production deployment with RDS, ElastiCache, ECS, and load balancing

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment to use remote state in S3
  # backend "s3" {
  #   bucket         = "blackroad-terraform-state"
  #   key            = "prod/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "BlackRoad"
      ManagedBy   = "Terraform"
    }
  }
}

# VPC and Networking
module "networking" {
  source = "./modules/networking"

  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = data.aws_availability_zones.available.names
}

# RDS PostgreSQL
module "rds" {
  source = "./modules/rds"

  project_name              = var.project_name
  environment               = var.environment
  instance_class            = var.rds_instance_class
  allocated_storage         = var.rds_allocated_storage
  backup_retention_period   = var.rds_backup_retention
  multi_az                  = var.rds_multi_az
  db_subnet_group_id        = module.networking.db_subnet_group_id
  security_group_ids        = [module.networking.database_security_group_id]
  db_name                   = "blackroad"
  db_username               = var.rds_username
  db_password               = var.rds_password
  skip_final_snapshot       = var.environment != "prod"
  enable_cloudwatch_logs    = true
  enable_performance_insights = true
}

# ElastiCache Redis
module "elasticache" {
  source = "./modules/elasticache"

  project_name              = var.project_name
  environment               = var.environment
  engine_version            = "7.0"
  node_type                 = var.redis_node_type
  num_cache_nodes           = var.redis_num_nodes
  subnet_group_name         = module.networking.elasticache_subnet_group_name
  security_group_ids        = [module.networking.redis_security_group_id]
  automatic_failover        = var.environment == "prod"
  transit_encryption        = true
  at_rest_encryption        = true
}

# ECS Cluster and Services
module "ecs" {
  source = "./modules/ecs"

  project_name              = var.project_name
  environment               = var.environment
  container_image           = var.container_image
  container_port            = 8000
  desired_task_count        = var.ecs_desired_count
  task_cpu                  = var.ecs_task_cpu
  task_memory               = var.ecs_task_memory
  vpc_id                    = module.networking.vpc_id
  private_subnet_ids        = module.networking.private_subnet_ids
  alb_security_group_id     = module.networking.alb_security_group_id
  ecs_security_group_id     = module.networking.ecs_security_group_id
  
  # Environment variables
  environment_variables = {
    DATABASE_URL  = "postgresql://${var.rds_username}@${module.rds.endpoint}/blackroad"
    REDIS_URL     = "redis://${module.elasticache.endpoint}:6379"
    ENVIRONMENT   = var.environment
    LOG_LEVEL     = var.log_level
  }
  
  # Secrets from AWS Secrets Manager
  secrets = {
    CLERK_API_KEY           = aws_secretsmanager_secret.clerk_api_key.arn
    STRIPE_SECRET_KEY       = aws_secretsmanager_secret.stripe_secret_key.arn
    STRIPE_WEBHOOK_SECRET   = aws_secretsmanager_secret.stripe_webhook_secret.arn
    RDS_PASSWORD            = aws_secretsmanager_secret.rds_password.arn
  }
  
  # Monitoring
  enable_cloudwatch_logging = true
  log_retention_days        = 30
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

# Secrets Manager
resource "aws_secretsmanager_secret" "clerk_api_key" {
  name                    = "${var.project_name}-clerk-api-key"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret" "stripe_secret_key" {
  name                    = "${var.project_name}-stripe-secret-key"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret" "stripe_webhook_secret" {
  name                    = "${var.project_name}-stripe-webhook-secret"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret" "rds_password" {
  name                    = "${var.project_name}-rds-password"
  recovery_window_in_days = 7
}

# Outputs
output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.endpoint
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.elasticache.endpoint
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = module.ecs.alb_dns_name
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}
