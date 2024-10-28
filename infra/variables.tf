variable "FASTLY_API_KEY" {
  type        = string
  description = "API key for the Fastly VCL edge configuration."
  sensitive   = true
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
variable "fastly_s3_logging" {
  type        = map(string)
  description = "S3 bucket keys for Fastly logging"
  sensitive   = true
}
variable "ngwaf_token" {
  type        = string
  description = "Secret token for the NGWAF API."
  sensitive   = true
}
