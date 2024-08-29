# DNS Module

This Terraform module sets up AWS Route53 resources for managing DNS records, 
supporting both apex domains and subdomains with Fastly CDN integration.

## Features

- Creates Route53 hosted zones for primary and user content (subdomain) domains
- Supports both apex domains and subdomains
- Automatically configures A/AAAA records for apex domains or CNAME for subdomains
- Integrates with Fastly CDN endpoints
- Provides a consistent set of name servers across hosted zones
- Allows addition of TXT records to the apex domain for verification purposes

## Usage

```hcl
module "CoolPythonWebsite" {
  source = "./dns"

  primary_domain      = "CoolPythonWebsite.com"
  user_content_domain = "users.CoolPythonWebsite.com"
  apex_txt            = ["v=spf1 include:_spf.example.com ~all"]
  tags                = {
    Environment = "Staging"
    Project     = "CoolPythonWebsite"
  }
}
```

## Input Variables

- `primary_domain`: Your main domain (e.g., "CoolPythonWebsite.com")
- `user_content_domain`: Domain for user-generated content (e.g., "users.CoolPythonWebsite.com")
- `apex_txt`: List of TXT records to add to the apex domain
- `tags`: Map of tags to apply to all created resources

## Outputs

- `primary_zone_id`: The Zone ID of the primary hosted zone
- `nameservers`: The set of name servers for your domains
- `user_content_zone_id`: The Zone ID of the user content hosted zone

## Requirements

Tested on 
- Terraform 1.8.5
- AWS provider ~> 5.0
