variable "aws_region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "eu-west-2"
}

variable "aws_profile" {
  description = "The AWS profile to use"
  type        = string
  default     = "tasman-dev"
}

variable "project" {
  description = "The name of the project"
  type        = string
  default     = "tasman-task"
}

variable "env" {
  description = "The environment (e.g. dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "bronze_bucket_name" {
  description = "The name of the S3 bucket for bronze data"
  type        = string
  default     = null
}
