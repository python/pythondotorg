provider "sigsci" {
  alias          = "firewall"
  corp           = var.NGWAF_CORP
  email          = var.NGWAF_EMAIL
  auth_token     = var.NGWAF_TOKEN
  fastly_api_key = var.FASTLY_API_KEY
}
