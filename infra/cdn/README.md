# Fastly CDN Config

This module creates Fastly services for the Python.org CDN.

## Usage
# Fastly VCL Terraform Module

This Terraform module configures a Fastly service using VCL (Varnish Configuration Language) for Python.org. It sets up a robust CDN configuration with various features to optimize performance, security, and logging.

## Features

- Configures Fastly VCL service for Python.org
- Supports multiple domains (primary and extra domains)
- Sets up backends with health checks
- Implements caching strategies and TTL configurations
- Configures HTTPS and HSTS
- Implements rate limiting
- Sets up logging to Datadog and S3
- Configures various headers and request/response manipulations
- Implements IP blocking capabilities

## Usage

```hcl
module "fastly_production" {
  source = "./cdn"

  name            = "CoolPythonApp.org"
  domain          = "CoolPythonApp.org"
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