locals {
  tags = {
    Application = "Python.org"
    Environment = "Production"
  }
}

locals {
  fastly_endpoints = {
    "python.map.fastly.net_A"     = ["151.101.128.223", "151.101.192.223", "151.101.0.223", "151.101.64.223"]
    "python.map.fastly.net_AAAA"  = ["2a04:4e42:200::223", "2a04:4e42:400::223", "2a04:4e42:600::223", "2a04:4e42::223"]
    "python.map.fastly.net_CNAME" = ["dualstack.python.map.fastly.net"]
  }
  domain_map = {
    "python.org"      = "python.map.fastly.net"
    "test.python.org" = "python.map.fastly.net"
  }
}

module "dns" {
  # TODO: this doesn't accommodate for DNS management splits between environments
  source         = "./dns"
  tags           = local.tags
  primary_domain = "python.org"
  zone_id         = module.dns.primary_zone_id
  fastly_endpoints = local.fastly_endpoints
  domain_map       = local.domain_map

  aws_access_key = var.AWS_ACCESS_KEY_ID
  aws_secret_key = var.AWS_SECRET_ACCESS_KEY

  # TODO: the below needs to be parameterized or fixed
  apex_txt = []
  domain = ""
  name = ""
  user_content_domain = ""
}

module "fastly_production" {
  source = "./cdn"

  name               = "Python.org"
  domain             = "python.org"
  extra_domains      = ["www.python.org"]
  backend_address    = "pythondotorg.ingress.us-east-2.psfhosted.computer"
  default_ttl        = 3600

  datadog_key  = var.DATADOG_API_KEY
  fastly_key   = var.FASTLY_API_KEY
  fastly_header_token = var.FASTLY_HEADER_TOKEN
  fastly_s3_logging = var.fastly_s3_logging
}

module "fastly_staging" {
  source = "./cdn"

  name               = "test.Python.org"
  domain             = "test.python.org"
  extra_domains      = []
  backend_address    = "test-pythondotorg.ingress.us-east-2.psfhosted.computer"
  default_ttl        = 3600

  datadog_key  = var.DATADOG_API_KEY
  fastly_key   = var.FASTLY_API_KEY
  fastly_header_token = var.FASTLY_HEADER_TOKEN
  fastly_s3_logging = var.fastly_s3_logging
}


# module "ngwaf" {
#   source = "./ngwaf"
#
# }
