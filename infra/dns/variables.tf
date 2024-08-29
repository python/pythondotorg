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
