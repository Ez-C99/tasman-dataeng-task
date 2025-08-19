# ADR 0001 — Runtime for the extractor

**Status:** Accepted  
**Date:** 2025-08-19  

## Context

The USAJOBS ETL may exceed 15 minutes when paging and enriching with codelists. We want the same artifact locally and in the cloud, with straightforward dependency management and reproducible runs.

## Decision

Use a containerized Python CLI packaged as a Docker image. Run locally via Docker Compose and in AWS via ECS Fargate.

## Options considered

- AWS Lambda (container image)
- EC2 + cron
- ECS Fargate (scheduled tasks)

## Consequences

- Avoid Lambda’s 15-minute ceiling; identical runtime locally and in cloud.
- Slightly more infrastructure than Lambda, but minimal ops burden.
- Straight path to scheduling with EventBridge → ECS RunTask.

## FoDE alignment

Choose common components wisely; reversible decisions; low operational complexity; plan for failure (re-runs are idempotent).

## Links

- Design doc: Runtime & Orchestration sections
- Superseded by: N/A

## References

MADR background; EventBridge to ECS schedule pattern.
