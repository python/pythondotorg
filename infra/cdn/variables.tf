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