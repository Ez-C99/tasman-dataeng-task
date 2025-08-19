############################################
# Trust policies (who can assume the roles)
############################################

# ECS tasks assume both roles
data "aws_iam_policy_document" "ecs_tasks_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

############################################
# Execution role (agent-level permissions)
############################################

resource "aws_iam_role" "ecs_execution_role" {
  name               = "${var.project}-${var.env}-ecs-exec"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_trust.json
  tags = { project = var.project, env = var.env }
}

# Attach AWS managed policy for pulling from ECR, sending logs, etc.
resource "aws_iam_role_policy_attachment" "ecs_exec_managed" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

############################################
# Task role (your app permissions)
############################################

resource "aws_iam_role" "ecs_task_role" {
  name               = "${var.project}-${var.env}-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_trust.json
  tags = { project = var.project, env = var.env }
}

# S3 Bronze RW policy (bucket-level + object-level statements)
data "aws_iam_policy_document" "bronze_rw" {
  # List operations live on the *bucket* ARN
  statement {
    sid     = "ListBucket"
    effect  = "Allow"
    actions = ["s3:ListBucket", "s3:ListBucketMultipartUploads"]
    resources = [aws_s3_bucket.bronze.arn]
    # (optional) scope list to the bronze/ prefix:
    # condition { test = "StringLike"; variable = "s3:prefix"; values = ["bronze/*"] }
  }

  # Object IO lives on the *objects* ARN
  statement {
    sid     = "ObjectIO"
    effect  = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:AbortMultipartUpload"
    ]
    resources = ["${aws_s3_bucket.bronze.arn}/*"]
  }
}

resource "aws_iam_policy" "task_bronze_policy" {
  name   = "${var.project}-${var.env}-bronze-rw"
  policy = data.aws_iam_policy_document.bronze_rw.json
}

resource "aws_iam_role_policy_attachment" "task_attach_bronze" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.task_bronze_policy.arn
}

############################################
# Outputs (use in ECS task definition later)
############################################
output "ecs_task_role_arn"      { value = aws_iam_role.ecs_task_role.arn }
output "ecs_execution_role_arn" { value = aws_iam_role.ecs_execution_role.arn }
