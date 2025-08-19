# ADR 0006 — Secrets management

**Status:** Accepted  
**Date:** 2025-08-19  

## Context

We need to store the USAJOBS API key and DB credentials securely and pass them to the container at runtime.

## Decision

Use AWS Secrets Manager. Reference secrets from the ECS task definition. Prefer injecting via the `secrets` mechanism; avoid hardcoding or committing secrets.

## Options considered

- Secrets Manager (chosen)
- SSM Parameter Store (viable alternative)
- Plain environment variables or files (not acceptable)

## Consequences

- Central rotation and auditing of secrets.
- ECS integrates natively with Secrets Manager.
- For high-sensitivity workloads, consider sidecar pattern to avoid env var exposure.

## FoDE alignment

Prioritize security; least privilege; audited, centralized secret storage.

## Links

- Design doc: Security & IaC sections
- Superseded by: N/A

## References

ECS + Secrets Manager injection; sensitive data patterns on ECS.
