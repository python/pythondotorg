variable "FASTLY_API_KEY" {
  type        = string
  description = "API key for the Fastly VCL edge configuration."
}
variable "FASTLY_HEADER_TOKEN" {
  description = "Fastly Token for authentication"
  type        = string
  sensitive   = true
}
variable "DATADOG_API_KEY" {
  type        = string
  description = "API key for Datadog logging"
  sensitive   = true
}