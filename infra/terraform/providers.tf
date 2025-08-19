terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # (optional now) S3 backend for remote state — add later when ready
  # backend "s3" {
  #   bucket = "<state-bucket>"
  #   key    = "tasman/infra/terraform.tfstate"
  #   region = "eu-west-2"
  #   # dynamodb_table = "<locks-table>"  # if you enable state locking
  # }
}

provider "aws" {
  region  = var.aws_region
  # If using a named profile locally:
  profile = var.aws_profile
  default_tags {
    tags = {
      project = var.project
      env     = var.env
    }
  }
}
