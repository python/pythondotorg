provider "aws" {
  alias      = "dns"
  region     = "us-east-2"
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
}
