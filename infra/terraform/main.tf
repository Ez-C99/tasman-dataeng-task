# ECS + ECR + EventBridge


# ECR Repository

resource "aws_ecr_repository" "etl" {
	name                 = "${var.project}-${var.env}-etl"
	image_tag_mutability = "MUTABLE"
	lifecycle { prevent_destroy = true }
}


# CloudWatch Log Group

resource "aws_cloudwatch_log_group" "etl" {
	name              = "/ecs/${var.project}-${var.env}-etl"
	retention_in_days = 30
}


# ECS Cluster

resource "aws_ecs_cluster" "etl" {
	name = "${var.project}-${var.env}-cluster"
}


# Security Group (egress only) - reuse default VPC discovered implicitly

data "aws_vpc" "default" { default = true }
data "aws_subnets" "default" {
	filter {
		name   = "vpc-id"
		values = [data.aws_vpc.default.id]
	}
}

resource "aws_security_group" "etl_task" {
	name        = "${var.project}-${var.env}-etl-sg"
	description = "ECS task egress"
	vpc_id      = data.aws_vpc.default.id

	egress {
		from_port   = 0
		to_port     = 0
		protocol    = "-1"
		cidr_blocks = ["0.0.0.0/0"]
	}
}


# Task Definition (Fargate)


locals {
	# Base environment vars (excluding DB_URL which is conditional)
	_base_env = [
		{ name = "USAJOBS_USER_AGENT", value = var.usajobs_user_agent },
		{ name = "BRONZE_S3_BUCKET",   value = aws_s3_bucket.bronze.bucket },
		{ name = "BRONZE_S3_PREFIX",   value = var.bronze_prefix },
		{ name = "DQ_ENFORCE",         value = tostring(var.dq_enforce) },
		{ name = "KEYWORD",            value = var.keyword },
		{ name = "LOCATION_NAME",      value = var.location_name },
		{ name = "MAX_PAGES",          value = tostring(var.max_pages) },
	]

	# Add DB_URL only when NOT using a secret and a fallback value provided
	container_env = concat(
		local._base_env,
		(var.db_url_secret_name == "" && var.db_url != "") ? [
			{ name = "DB_URL", value = var.db_url }
		] : []
	)

	container_defs = [{
		name      = "etl"
		image     = "${aws_ecr_repository.etl.repository_url}:latest"
		essential = true
		environment = local.container_env
		secrets = concat(
			var.usajobs_auth_secret_name != "" && local.usajobs_auth_secret_arn != "" ? [
				{
					name      = "USAJOBS_AUTH_KEY"
					valueFrom = local.usajobs_auth_secret_arn
				}
			] : [],
			var.db_url_secret_name != "" && local.db_url_secret_arn != "" ? [
				{
					name      = "DB_URL"
					valueFrom = local.db_url_secret_arn
				}
			] : []
		)
		logConfiguration = {
			logDriver = "awslogs"
			options = {
				awslogs-group         = aws_cloudwatch_log_group.etl.name
				awslogs-region        = var.aws_region
				awslogs-stream-prefix = "ecs"
			}
		}
	}]
}

resource "aws_ecs_task_definition" "etl" {
	family                   = "${var.project}-${var.env}-etl"
	cpu                      = tostring(var.container_cpu)
	memory                   = tostring(var.container_memory)
	network_mode             = "awsvpc"
	requires_compatibilities = ["FARGATE"]
	execution_role_arn       = aws_iam_role.ecs_execution_role.arn
	task_role_arn            = aws_iam_role.ecs_task_role.arn
	runtime_platform {
		operating_system_family = "LINUX"
		cpu_architecture        = "X86_64"
	}
	container_definitions = jsonencode(local.container_defs)
}


# EventBridge Schedule triggering RunTask

resource "aws_cloudwatch_event_rule" "etl_schedule" {
	name                = "${var.project}-${var.env}-etl-schedule"
	schedule_expression = var.schedule_expression
}

data "aws_iam_policy_document" "events_assume" {
	statement {
		actions = ["sts:AssumeRole"]
		principals {
			type        = "Service"
			identifiers = ["events.amazonaws.com"]
		}
	}
}

resource "aws_iam_role" "events_invoke" {
	name               = "${var.project}-${var.env}-events-invoke"
	assume_role_policy = data.aws_iam_policy_document.events_assume.json
}

data "aws_iam_policy_document" "events_run_task" {
	statement {
		sid       = "RunTask"
		actions   = ["ecs:RunTask"]
		# Allow running the current task definition revision (this updates automatically on new revision apply)
		resources = [aws_ecs_task_definition.etl.arn]
		condition {
			test     = "ArnEquals"
			variable = "ecs:cluster"
			values   = [aws_ecs_cluster.etl.arn]
		}
	}
	statement {
		sid       = "PassRoles"
		actions   = ["iam:PassRole"]
		resources = [aws_iam_role.ecs_execution_role.arn, aws_iam_role.ecs_task_role.arn]
	}
}

resource "aws_iam_policy" "events_run_task" {
	name   = "${var.project}-${var.env}-events-run-task"
	policy = data.aws_iam_policy_document.events_run_task.json
}

resource "aws_iam_role_policy_attachment" "events_run_task_attach" {
	role       = aws_iam_role.events_invoke.name
	policy_arn = aws_iam_policy.events_run_task.arn
}

resource "aws_cloudwatch_event_target" "etl" {
	rule      = aws_cloudwatch_event_rule.etl_schedule.name
	target_id = "${var.project}-${var.env}-etl-target"
	arn       = aws_ecs_cluster.etl.arn
	role_arn  = aws_iam_role.events_invoke.arn
	ecs_target {
		launch_type         = "FARGATE"
		platform_version    = "LATEST"
		task_definition_arn = aws_ecs_task_definition.etl.arn
		enable_execute_command = false
		network_configuration {
			subnets          = data.aws_subnets.default.ids
			security_groups  = [aws_security_group.etl_task.id]
			assign_public_ip = true
		}
	}
	depends_on = [aws_ecs_task_definition.etl, aws_iam_role.events_invoke]
}


# Outputs

output "ecr_repo_url" { value = aws_ecr_repository.etl.repository_url }
output "ecs_cluster_arn" { value = aws_ecs_cluster.etl.arn }
output "task_definition_arn" { value = aws_ecs_task_definition.etl.arn }
output "event_rule_name" { value = aws_cloudwatch_event_rule.etl_schedule.name }
output "log_group" { value = aws_cloudwatch_log_group.etl.name }
