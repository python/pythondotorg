
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
  type        = string
  description = "S3 bucket keys for Fastly logging"
  sensitive   = true
}
variable "AWS_ACCESS_KEY_ID" {
  type        = string
  description = "Access key for the AWS account."
  sensitive   = true
  default = "awd"
}

variable "AWS_SECRET_ACCESS_KEY" {
  type        = string
  description = "Secret access key for the AWS account."
  sensitive   = true
}