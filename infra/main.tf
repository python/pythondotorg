variable "fastly_s3_logging" { type = map(any) }

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
  source         = "./dns"
  tags           = local.tags
  primary_domain = "python.org"
}

module "pythondotorg_production" {
  source = "./cdn"

  name               = "Python.org"
  domain             = "python.org"
  extra_domains      = ["www.python.org"]
  backend_address    = "pythondotorg.ingress.us-east-2.psfhosted.computer"
  default_ttl        = 3600
  stale_if_error     = false
  stale_if_error_ttl = 43200

  zone_id         = module.dns.primary_zone_id
  backend         = "pythondotorg.ingress.us-east-2.psfhosted.computer"
  s3_logging_keys = var.fastly_s3_logging

  fastly_endpoints = local.fastly_endpoints
  domain_map       = local.domain_map
}

module "pythondotorg_staging" {
  source = "./cdn"

  name               = "test.Python.org"
  domain             = "test.python.org"
  extra_domains      = []
  backend_address    = "test-pythondotorg.ingress.us-east-2.psfhosted.computer"
  default_ttl        = 3600
  stale_if_error     = false
  stale_if_error_ttl = 43200

  zone_id         = module.dns.primary_zone_id
  backend         = "test-pythondotorg.ingress.us-east-2.psfhosted.computer"
  s3_logging_keys = var.fastly_s3_logging

  fastly_endpoints = local.fastly_endpoints
  domain_map       = local.domain_map
}


# module "ngwaf" {
#   source = "./ngwaf"
#
# }
