# Architecture Decision Records (ADR) — Index

This directory contains atomic, versioned **Architecture Decision Records** (ADRs) for the Tasman USAJOBS ETL. Each ADR captures the context, options, decision, and consequences for an architecturally significant choice. See the MADR template for background.

## Table of Contents

- [ADR 0001 — Runtime for the extractor](./0001-runtime-extractor.md) — **Accepted**
- [ADR 0002 — Scheduling & orchestration](./0002-scheduling.md) — **Accepted**
- [ADR 0003 — Operational data store](./0003-database.md) — **Accepted**
- [ADR 0004 — Data model shape](./0004-data-model-shape.md) — **Accepted**
- [ADR 0005 — Idempotency and primary key strategy](./0005-idempotency-key-upsert.md) — **Accepted**
- [ADR 0006 — Secrets management](./0006-secrets-management.md) — **Accepted**
- [ADR 0007 — API paging and limits](./0007-api-paging-and-limits.md) — **Accepted**
- [ADR 0008 — Database security and durability](./0008-db-security-and-durability.md) — **Accepted**
- [ADR 0009 — Data quality strategy](./0009-data-quality.md) — **Accepted**
- [ADR 0010 — Integration testing approach](./0010-integration-testing.md) — **Accepted**

## Working with ADRs

- New ADRs live here as `NNNN-title.md` (e.g., `0011-xyz.md`).  
- Keep each ADR short; link to PRs and the main design doc for detail.  
- To supersede a decision, add a new ADR and mark the old one **Superseded by** the new ID.

## Link checking

Use the `make links` target in the repo root to validate all links in this folder (and other docs).
