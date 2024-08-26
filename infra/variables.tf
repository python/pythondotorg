# Fastly variables
variable "FASTLY_API_KEY" {
  type        = string
  description = "API key for the Fastly VCL edge configuration."
}
variable "FASTLY_HEADER_TOKEN" {
  description = "Fastly Token for authentication"
  type        = string
  sensitive   = true
}

# VCL Service variables
variable "USER_VCL_SERVICE_DOMAIN_NAME" {
  type        = string
  description = "Frontend domain for your service."
  default     = "ngwaftest.psf.io"
}

variable "USER_VCL_SERVICE_BACKEND_HOSTNAME" {
  type        = string
  description = "Hostname used for backend."
  default     = "test-ngwaf.psf.io"
}

variable "Edge_Security_dictionary" {
  type    = string
  default = "Edge_Security"
}

# NGWAF variables
variable "NGWAF_CORP" {
  type        = string
  description = "Corp name for NGWAF"
  default     = "python"
}

variable "NGWAF_SITE" {
  type        = string
  description = "Site SHORT name for NGWAF"
  default     = "test"
}

variable "NGWAF_EMAIL" {
  type        = string
  description = "Email address associated with the token for the NGWAF API."
  default     = "jacob.coffee@pyfound.org"
}

variable "NGWAF_TOKEN" {
  type        = string
  description = "Secret token for the NGWAF API."
  sensitive   = true
}

# AWS variables
variable "AWS_ACCESS_KEY_ID" {
  type        = string
  description = "Access key for the AWS account."
  sensitive   = true
}

variable "AWS_SECRET_ACCESS_KEY" {
  type        = string
  description = "Secret access key for the AWS account."
  sensitive   = true
}

variable "route53_zone_id" {
  type        = string
  description = "The Route 53 hosted zone ID"
  default     = "Z2LSM2W8Q3WN11" # psf.io
}

variable "route53_record_name" {
  type        = string
  description = "The name of the CNAME record"
  default     = "ngwaftest.psf.io"
}

variable "route53_record_ttl" {
  type        = number
  description = "The TTL for the CNAME record"
  default     = 60
}