# ADR 0003 — Operational data store

**Status:** Accepted  
**Date:** 2025-08-19  

## Context

We need durable storage with ACID semantics, robust upsert, and strong support for semi-structured payloads (raw job descriptors) alongside curated relational tables.

## Decision

Use PostgreSQL (AWS RDS Postgres / Aurora Postgres).

## Options considered

- PostgreSQL
- MySQL
- Microsoft SQL Server

## Consequences

- Use JSONB + GIN indexes for flexible querying, and `INSERT ... ON CONFLICT` for idempotent upserts.
- Broad OSS ecosystem and local parity for testing.
- Straightforward SSL/TLS and encryption at rest on RDS.

## FoDE alignment

Choose components that fit expected data shape; build for evolvability and correctness.

## Links

- Design doc: DBMS choice and schema sections
- Superseded by: N/A

## References

Postgres GIN & JSONB; ON CONFLICT upsert.
