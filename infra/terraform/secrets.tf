# Secrets Manager handling for USAJOBS auth key.
# Modes:
# Existing secret (recommended): set var.usajobs_auth_secret_name and leave var.usajobs_auth_key empty.
# Terraform uses a data source and does NOT manage the secret value.

locals {
  _want_secret          = var.usajobs_auth_secret_name != ""
  _manage_secret_value  = local._want_secret && var.usajobs_auth_key != ""
}

# Data source for existing secret (created outside TF)
data "aws_secretsmanager_secret" "usajobs_auth" {
  count = local._want_secret && !local._manage_secret_value ? 1 : 0
  name  = var.usajobs_auth_secret_name
}

# Managed secret resources (only if a key provided)
resource "aws_secretsmanager_secret" "usajobs_auth" {
  count       = local._manage_secret_value ? 1 : 0
  name        = var.usajobs_auth_secret_name
  description = "USAJOBS API auth key"
  tags        = { project = var.project, env = var.env }
}

resource "aws_secretsmanager_secret_version" "usajobs_auth" {
  count         = local._manage_secret_value ? 1 : 0
  secret_id     = aws_secretsmanager_secret.usajobs_auth[0].id
  secret_string = var.usajobs_auth_key
}

# Canonical secret ARN (resource or data)
locals {
  usajobs_auth_secret_arn = local._manage_secret_value ? aws_secretsmanager_secret.usajobs_auth[0].arn : (
    local._want_secret ? data.aws_secretsmanager_secret.usajobs_auth[0].arn : ""
  )
}

# DB URL secret (existing only; we don't manage value here)
data "aws_secretsmanager_secret" "db_url" {
  count = var.db_url_secret_name != "" ? 1 : 0
  name  = var.db_url_secret_name
}

locals {
  db_url_secret_arn = var.db_url_secret_name != "" ? data.aws_secretsmanager_secret.db_url[0].arn : ""
}
