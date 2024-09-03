variable "aws_access_key" {
  type        = string
  description = "Access key for the AWS account."
  sensitive   = true
}

variable "aws_secret_key" {
  type        = string
  description = "Secret access key for the AWS account."
  sensitive   = true
}

variable "route53_zone_id" {
  type        = string
  description = "The Route 53 hosted zone ID"
  default     = "Z3JUI7A2G39FQL" # python.org
}

variable "route53_record_name" {
  type        = string
  description = "The name of the CNAME record"
  default     = "test.python.org"
}

variable "route53_record_ttl" {
  type        = number
  description = "The TTL for the CNAME record"
  default     = 60
}

variable "tags" {
  type        = map(any)
  description = "Tags to apply to all resources"
}
variable "primary_domain" {
  type        = string
  description = "The primary domain name"
}
variable "user_content_domain" {
  type        = string
  description = "The user content (sub)domain name"
}
variable "apex_txt" {
  type        = list(any)
  description = "The TXT record for the apex domain"
}
variable "name" {
  type        = string
  description = "The name of the Fastly service"
}
variable "zone_id" {
  type        = string
  description = "The Route 53 hosted zone ID"
}
variable "domain" {
  type        = string
  description = "The domain name of the service"
}
variable "fastly_endpoints" {
  type        = map(any)
  description = "The Fastly endpoints"
}
variable "domain_map" {
  type        = map(any)
  description = "The domain map"
}