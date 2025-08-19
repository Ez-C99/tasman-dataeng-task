# ADR 0002 — Scheduling & orchestration

**Status:** Accepted  
**Date:** 2025-08-19  

## Context

We need a daily run with retries and simple failure alerts. The pipeline has one primary step today (extract→load), but may later add validation, notify, or other steps.

## Decision

Use Amazon EventBridge to trigger an ECS Fargate RunTask on a cron schedule.

## Options considered

- EventBridge schedule → ECS RunTask
- AWS Step Functions (state machine)
- Self-managed scheduler inside the container (cron)

## Consequences

- Minimal services and cost for a single-step job.
- Can evolve to Step Functions later if we add multiple chained steps.
- Native retry/visibility via CloudWatch and EventBridge.

## FoDE alignment

Loosely coupled components; “always be architecting”; plan for failure (retries/alerts).

## Links

- Design doc: Orchestration section
- Superseded by: N/A

## References

EventBridge scheduled rule targeting ECS RunTask; creating cron rules.
