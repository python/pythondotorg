module "fastly_production" {
  source = "./cdn"

  name            = "Python.org"
  domain          = "python.org"
  extra_domains   = ["www.python.org"]
  backend_address = "pythondotorg.ingress.us-east-2.psfhosted.computer"
  default_ttl     = 3600

  datadog_key         = var.DATADOG_API_KEY
  fastly_key          = var.FASTLY_API_KEY
  fastly_header_token = var.FASTLY_HEADER_TOKEN
  s3_logging_keys     = var.fastly_s3_logging
}

module "fastly_staging" {
  source = "./cdn"

  name            = "test.Python.org"
  domain          = "test.python.org"
  extra_domains   = []
  # TODO: adjust to test-pythondotorg when done testing NGWAF
  backend_address = "pythondotorg.ingress.us-east-2.psfhosted.computer"
  default_ttl     = 3600

  datadog_key         = var.DATADOG_API_KEY
  fastly_key          = var.FASTLY_API_KEY
  fastly_header_token = var.FASTLY_HEADER_TOKEN
  s3_logging_keys     = var.fastly_s3_logging
}
