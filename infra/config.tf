# Connect us to TF Cloud for remote deploys
terraform {
  cloud {
    organization = "psf"
    workspaces {
      name = "pythondotorg-infra"
    }
  }
}
