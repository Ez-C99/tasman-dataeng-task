
variable "project" {
  description = "The name of the project"
  type        = string
}

variable "env" {
  description = "The environment (e.g. dev, staging, prod)"
  type        = string
}

variable "bronze_bucket_name" {
  description = "The name of the S3 bucket for bronze data"
  type        = string
  default     = nuill
}
