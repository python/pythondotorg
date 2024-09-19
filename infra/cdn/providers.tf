provider "fastly" {
  alias   = "cdn"
  api_key = var.fastly_key
}

provider "sigsci" {
  alias          = "firewall"
  corp           = var.ngwaf_corp_name
  email          = var.ngwaf_email
  auth_token     = var.ngwaf_token
  fastly_api_key = var.fastly_key
}
