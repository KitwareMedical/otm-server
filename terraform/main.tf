
terraform {
  backend "remote" {
    hostname     = "app.terraform.io"
    organization = "kitware-otm"

    workspaces {
      name = "optimal-transport-morphometry"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

provider "heroku" {}

data "aws_route53_zone" "kitware_otm" {
  name = "kitware-otm.org"
}
