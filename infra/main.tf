terraform {
  required_providers {
    fastly = {
      source  = "fastly/fastly"
      version = "5.13.0"
    }
    sigsci = {
      source  = "signalsciences/sigsci"
      version = "3.3.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Provider configurations
provider "fastly" {
  api_key = var.FASTLY_API_KEY
}

provider "aws" {
  region     = "us-east-2"
  access_key = var.AWS_ACCESS_KEY_ID
  secret_key = var.AWS_SECRET_ACCESS_KEY
}

provider "sigsci" {
  corp         = var.NGWAF_CORP
  email        = var.NGWAF_EMAIL
  auth_token   = var.NGWAF_TOKEN
  fastly_api_key = var.FASTLY_API_KEY
}