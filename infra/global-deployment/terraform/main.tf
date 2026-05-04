# Multi-Region AWS Infrastructure - Terraform Configuration
# Deploys Blackroad platform across 6 AWS regions

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    bucket         = "blackroad-terraform-state"
    key            = "global-deployment/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

# Define regions
locals {
  regions = {
    us-east-1 = {
      name           = "N. Virginia"
      azs            = 3
      instance_count = 10
      cidr_block     = "10.0.0.0/16"
      is_primary     = true
    }
    us-west-2 = {
      name           = "N. California"
      azs            = 2
      instance_count = 8
      cidr_block     = "10.1.0.0/16"
      is_primary     = false
    }
    eu-west-1 = {
      name           = "Ireland"
      azs            = 3
      instance_count = 8
      cidr_block     = "10.2.0.0/16"
      is_primary     = false
    }
    ap-southeast-1 = {
      name           = "Singapore"
      azs            = 2
      instance_count = 6
      cidr_block     = "10.3.0.0/16"
      is_primary     = false
    }
    ap-northeast-1 = {
      name           = "Tokyo"
      azs            = 2
      instance_count = 6
      cidr_block     = "10.4.0.0/16"
      is_primary     = false
    }
    sa-east-1 = {
      name           = "São Paulo"
      azs            = 2
      instance_count = 4
      cidr_block     = "10.5.0.0/16"
      is_primary     = false
    }
  }

  tags = {
    Project     = "Blackroad"
    Environment = "Production"
    ManagedBy   = "Terraform"
  }
}

# Module for each region
module "regional_deployment" {
  for_each = local.regions

  source = "./modules/regional-deployment"

  region              = each.key
  region_name         = each.value.name
  availability_zones  = each.value.azs
  instance_count      = each.value.instance_count
  cidr_block          = each.value.cidr_block
  is_primary          = each.value.is_primary
  instance_type       = "t3.medium"
  database_instance   = "db.r5.large"
  
  tags = local.tags
}

# Global resources
provider "aws" {
  region = "us-east-1"
  alias  = "global"
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# CloudFlare Zone for DNS
resource "cloudflare_zone" "main" {
  account_id = var.cloudflare_account_id
  zone       = "blackroad.io"
}

# CloudFlare Global Load Balancer
resource "cloudflare_load_balancer" "global" {
  zone_id = cloudflare_zone.main.id
  name    = "api.blackroad.io"
  ttl     = 30
  default_pool_ids = [
    cloudflare_load_balancer_pool.us_east.id,
    cloudflare_load_balancer_pool.eu_west.id
  ]
  description = "Global load balancer for Blackroad API"
  steering_policy = "geo"

  region_pools {
    region   = "WNAM"
    pool_ids = [cloudflare_load_balancer_pool.us_east.id]
  }

  region_pools {
    region   = "ENAM"
    pool_ids = [cloudflare_load_balancer_pool.us_east.id]
  }

  region_pools {
    region   = "WEUR"
    pool_ids = [cloudflare_load_balancer_pool.eu_west.id]
  }

  region_pools {
    region   = "EASIA"
    pool_ids = [cloudflare_load_balancer_pool.ap_southeast.id]
  }
}

# Regional load balancer pools
resource "cloudflare_load_balancer_pool" "us_east" {
  account_id = var.cloudflare_account_id
  name       = "us-east-1-pool"
  monitor    = cloudflare_load_balancer_monitor.health_check.id

  origins {
    name    = "us-east-1"
    address = module.regional_deployment["us-east-1"].load_balancer_dns
    enabled = true
  }

  check_regions = ["WNAM", "ENAM", "WEU", "EASIA"]
}

resource "cloudflare_load_balancer_pool" "eu_west" {
  account_id = var.cloudflare_account_id
  name       = "eu-west-1-pool"
  monitor    = cloudflare_load_balancer_monitor.health_check.id

  origins {
    name    = "eu-west-1"
    address = module.regional_deployment["eu-west-1"].load_balancer_dns
    enabled = true
  }

  check_regions = ["WEU", "EASIA"]
}

resource "cloudflare_load_balancer_pool" "ap_southeast" {
  account_id = var.cloudflare_account_id
  name       = "ap-southeast-1-pool"
  monitor    = cloudflare_load_balancer_monitor.health_check.id

  origins {
    name    = "ap-southeast-1"
    address = module.regional_deployment["ap-southeast-1"].load_balancer_dns
    enabled = true
  }

  check_regions = ["EASIA"]
}

# Health check monitor
resource "cloudflare_load_balancer_monitor" "health_check" {
  account_id = var.cloudflare_account_id
  type       = "https"
  port       = 443
  method     = "GET"
  path       = "/health"
  interval   = 30
  timeout    = 5
  retries    = 2

  expected_codes = "200"
  description    = "Health check for Blackroad API"

  allow_insecure = false
  follow_redirects = false
}

# CloudFlare CDN Rules
resource "cloudflare_page_rule" "cdn_cache" {
  zone_id = cloudflare_zone.main.id
  target  = "api.blackroad.io/static/*"
  actions {
    cache_level = "cache_everything"
  }
}

resource "cloudflare_page_rule" "api_no_cache" {
  zone_id = cloudflare_zone.main.id
  target  = "api.blackroad.io/api/*"
  actions {
    cache_level = "bypass"
  }
}

# Outputs
output "global_api_endpoint" {
  value       = "https://api.blackroad.io"
  description = "Global API endpoint (routed via CloudFlare)"
}

output "regional_endpoints" {
  value = {
    for region, deployment in module.regional_deployment :
    region => deployment.load_balancer_dns
  }
  description = "Regional load balancer endpoints"
}

output "cloudflare_nameservers" {
  value       = cloudflare_zone.main.name_servers
  description = "CloudFlare nameservers for DNS delegation"
}
