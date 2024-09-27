module "fastly_production" {
  source = "./cdn"

  name            = "www.python.org"
  domain          = "python.org"
  subdomain       = "www.python.org"
  extra_domains   = ["www.python.org"]
  backend_address = "pythondotorg.ingress.us-east-2.psfhosted.computer"
  default_ttl     = 3600

  datadog_key         = var.DATADOG_API_KEY
  fastly_key          = var.FASTLY_API_KEY
  fastly_header_token = var.FASTLY_HEADER_TOKEN
  s3_logging_keys     = var.fastly_s3_logging

  ngwaf_site_name        = "pythondotorg-prod"
  ngwaf_email            = "infrastructure-staff@python.org"
  ngwaf_token            = var.ngwaf_token
  activate_ngwaf_service = true
}

module "fastly_staging" {
  source = "./cdn"

  name          = "test.python.org"
  domain        = "test.python.org"
  subdomain     = "www.test.python.org"
  extra_domains = ["www.test.python.org"]
  # TODO: adjust to test-pythondotorg when done testing NGWAF
  backend_address = "pythondotorg.ingress.us-east-2.psfhosted.computer"
  default_ttl     = 3600

  datadog_key         = var.DATADOG_API_KEY
  fastly_key          = var.FASTLY_API_KEY
  fastly_header_token = var.FASTLY_HEADER_TOKEN
  s3_logging_keys     = var.fastly_s3_logging

  ngwaf_site_name        = "pythondotorg-test"
  ngwaf_email            = "infrastructure-staff@python.org"
  ngwaf_token            = var.ngwaf_token
  activate_ngwaf_service = true
}
