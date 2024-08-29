# This Terraform configuration sets up AWS Route53 resources
# ? TODO: It may be nice to allow a var when sourcing this module to
#         force destroy/allow overwriting of existing resources

# Retrieve the current AWS account data (based on secrets provided in .tfvars or TF Cloud)
data "aws_caller_identity" "current" {}

# Input variables passed in from `$root/infra/main.tf`
variable "tags" { type = map(any) }
variable "primary_domain" { type = string }
variable "user_content_domain" { type = string }
variable "apex_txt" { type = list(any) }
variable "name" { type = string }
variable "zone_id" { type = string }
variable "domain" { type = string }
variable "fastly_endpoints" { type = map(any) }
variable "domain_map" { type = map(any) }

# see if we're dealing with an apex domain or subdomain by splitting the domain name and counting the parts
locals {
  apex_domain = length(split(".", var.domain)) > 2 ? false : true
}

# Create a reusable set of nameservers
# This ensures consistent NS across multiple hosted zones
resource "aws_route53_delegation_set" "ns" {}

resource "aws_route53_zone" "primary" {
  name              = var.domain
  delegation_set_id = aws_route53_delegation_set.ns.id
  tags              = var.tags
}

resource "aws_route53_zone" "user_content" {
  name              = var.user_content_domain
  delegation_set_id = aws_route53_delegation_set.ns.id
  tags              = var.tags
}

resource "aws_route53_record" "apex_txt" {
  zone_id = aws_route53_zone.primary.zone_id
  name    = var.primary_domain
  type    = "TXT"
  ttl     = 3600
  records = var.apex_txt
}

# Create the main DNS record, automatically choosing between A (for apex) and CNAME (for subdomain)
# depending on the value of `local.apex_domain` above
# This will point to our Fastly CDN endpoints
resource "aws_route53_record" "primary" {
  zone_id = var.zone_id
  name    = var.domain
  type    = local.apex_domain ? "A" : "CNAME"
  ttl     = 86400
  records = var.fastly_endpoints[join("_", concat([var.domain_map[var.domain]], [local.apex_domain ? "A" : "CNAME"]))]
}

# Same as above, but also create an AAAA record for IPv6
resource "aws_route53_record" "primary-ipv6" {
  count   = local.apex_domain ? 1 : 0
  zone_id = var.zone_id
  name    = var.domain
  type    = "AAAA"
  ttl     = 86400
  records = var.fastly_endpoints[join("_", [var.domain_map[var.domain], "AAAA"])]
}

# Output things we need to ref. elsewhere
output "primary_zone_id" {
  value       = aws_route53_record.primary.zone_id
  description = "The Zone ID of our primary hosted zone."
}

output "nameservers" {
  value       = aws_route53_delegation_set.ns.name_servers
  description = "The set of name servers for our domains."
}

output "user_content_zone_id" {
  value = aws_route53_zone.user_content.zone_id
}