# Fastly CDN Config

This module creates Fastly services for the Python.org staging and production instances.

## Usage

```hcl
module "fastly_production" {
  source = "./cdn"

  name            = "CoolPythonApp.org"
  domain          = "CoolPythonApp.org"
  subdomain       = "www.CoolPythonApp.org"
  extra_domains   = ["www.CoolPythonApp.org"]
  backend_address = "service.CoolPythonApp.org"
  default_ttl     = 3600

  datadog_key         = var.DATADOG_API_KEY
  fastly_key          = var.FASTLY_API_KEY
  fastly_header_token = var.FASTLY_HEADER_TOKEN
  s3_logging_keys     = var.fastly_s3_logging
}
```

## Outputs

N/A

## Requirements

Tested on 
- Tested on Terraform 1.8.5
- Fastly provider 5.13.0