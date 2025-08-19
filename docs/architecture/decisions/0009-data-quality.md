# ADR 0009 — Data quality strategy

**Status:** Accepted  
**Date:** 2025-08-19  

## Context

We want early detection of shape/type issues and human-readable validations without heavy overhead.

## Decision

Validate payloads with Pydantic models during parsing and add a small Great Expectations suite before loading (non-nulls, numeric ranges, sane lat/lon, at least one location).

## Options considered

- Pydantic + Great Expectations (chosen)
- Only ad-hoc asserts in code (insufficient)
- Heavy governance stack (out of scope)

## Consequences

- Fast feedback loops in dev/CI; portable validation artifacts.
- Can grow to table-level constraints and dbt tests later.

## FoDE alignment

DataOps mindset; shift-left data quality; incremental governance.

## Links

- Design doc: Testing & Data Quality sections
- Superseded by: N/A

## References

Great Expectations quickstart (GX OSS).
