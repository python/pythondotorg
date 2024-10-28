variable "fastly_key" {
  type        = string
  description = "API key for the Fastly VCL edge configuration."
}
variable "fastly_header_token" {
  description = "Fastly header token ensure we only allow Fastly to access the service"
  type        = string
  sensitive   = true
}
variable "datadog_key" {
  type        = string
  description = "API key for Datadog logging"
  sensitive   = true
}
variable "s3_logging_keys" {
  type        = map(string)
  description = "S3 bucket keys for Fastly logging"
  sensitive   = true
}
variable "name" {
  type        = string
  description = "The name of the Fastly service."
}
variable "domain" {
  type        = string
  description = "The domain name of the service."
}
variable "subdomain" {
  type        = string
  description = "The subdomain of the service."
}
variable "extra_domains" {
  type        = list(string)
  description = "Extra domains to add to the service."
}
variable "backend_address" {
  type        = string
  description = "The hostname of the backend service."
}
variable "default_ttl" {
  type        = number
  description = "The default TTL for the service."
}

## NGWAF
variable "activate_ngwaf_service" {
  type        = bool
  description = "Whether to activate the NGWAF service."
}
variable "edge_security_dictionary" {
  type        = string
  description = "The dictionary name for the Edge Security product."
  default     = "Edge_Security"
}
variable "ngwaf_corp_name" {
  type        = string
  description = "Corp name for NGWAF"
  default     = "python"
}
variable "ngwaf_site_name" {
  type        = string
  description = "Site SHORT name for NGWAF"

  validation {
    condition     = can(regex("^(pythondotorg-test|pythondotorg-prod)$", var.ngwaf_site_name))
    error_message = "'ngwaf_site_name' must be one of the following: pythondotorg-test, or pythondotorg-prod"
  }
}
variable "ngwaf_email" {
  type        = string
  description = "Email address associated with the token for the NGWAF API."
}
variable "ngwaf_token" {
  type        = string
  description = "Secret token for the NGWAF API."
  sensitive   = true
}
