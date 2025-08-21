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

# --- Added for ECS / scheduler deployment ---
variable "schedule_expression" {
  description = "EventBridge schedule (cron or rate)"
  type        = string
  default = "cron(0 0 * * ? *)"
}

variable "dq_enforce" {
  description = "Enforce data quality gate"
  type        = bool
  default     = true
}

variable "bronze_prefix" {
  description = "Bronze S3 prefix"
  type        = string
  default     = "bronze/usajobs"
}

variable "usajobs_user_agent" {
  description = "USAJOBS registered email (User-Agent)"
  type        = string
}

variable "usajobs_auth_key" {
  description = "(DEPRECATED) Direct USAJOBS API auth key. Prefer secrets manager."
  type        = string
  default     = ""
}

variable "usajobs_auth_secret_name" {
  description = "Secrets Manager secret name storing USAJOBS auth key"
  type        = string
  default     = "tasman/dev/usajobs/auth"
}

variable "db_url" {
  description = "Database URL for Postgres"
  type        = string
  # Optional: if using Secrets Manager (db_url_secret_name) this can be left blank.
  # Providing both a secret and this value will prefer the secret at runtime.
  default     = ""
}

variable "db_url_secret_name" {
  description = "Secrets Manager secret name containing full DB URL"
  type        = string
  default     = "tasman/dev/db/url"
}

variable "container_cpu" {
  description = "Fargate task CPU units"
  type        = number
  default     = 512
}

variable "container_memory" {
  description = "Fargate task memory (MB)"
  type        = number
  default     = 1024
}

variable "keyword" {
  description = "Default search keyword"
  type        = string
  default     = "data"
}

variable "location_name" {
  description = "Default location name"
  type        = string
  default     = "Chicago"
}

variable "max_pages" {
  description = "Max pages per run"
  type        = number
  default     = 1
}
