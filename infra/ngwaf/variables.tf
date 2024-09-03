variable "service_name" {
  type = string
}

variable "USER_VCL_SERVICE_DOMAIN_NAME" {
  type        = string
  description = "The domain name of the service."
}

variable "USER_VCL_SERVICE_BACKEND_HOSTNAME" {
  type        = string
  description = "The hostname of the backend service."
}

variable "Edge_Security_dictionary" {
  type        = string
  description = "The dictionary name for the Edge Security product."
}

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
}

variable "NGWAF_TOKEN" {
  type        = string
  description = "Secret token for the NGWAF API."
  sensitive   = true
}

variable "FASTLY_API_KEY" {
  type        = string
  description = "API key for the Fastly VCL edge configuration."
}
