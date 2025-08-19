# ADR 0010 — Integration testing approach

**Status:** Accepted  
**Date:** 2025-08-19  

## Context

We need to verify DDL, constraints, and upsert behavior against a real Postgres engine in CI without managing databases manually.

## Decision

Use Testcontainers for Python to spin up Postgres in tests. Assert `ON CONFLICT` upserts and referential integrity across `job_*` tables.

## Options considered

- Testcontainers (chosen)
- Docker Compose in CI (heavier setup)
- Mock-only tests (insufficient coverage)

## Consequences

- High-fidelity integration tests with minimal CI plumbing.
- Parity with production engine & extensions.

## FoDE alignment

Software engineering hygiene; reproducibility and automation.

## Links

- Design doc: Testing plan
- Superseded by: N/A

## References

Testcontainers Python / Postgres modules.
