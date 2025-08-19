# ADR 0004 — Data model shape

**Status:** Accepted  
**Date:** 2025-08-19  

## Context

USAJOBS postings have multi-valued fields (locations, categories), long descriptive texts, and evolving structures. Flattening lists into comma-separated strings harms queryability and indexing.

## Decision

Adopt a lean normalized core:

- `job` (1:1)
- `job_location` (1:N)
- `job_category` (1:N)
- `job_details` (1:1)
Keep `raw_json` as JSONB for audit and flexible access.

## Options considered

- Two-table design (results + details)
- Lean normalized core (chosen)
- JSONB-only (schema-on-read)

## Consequences

- Slightly more joins and ETL code to explode lists.
- Much better filtering/indexing and future evolution.
- JSONB provides a safety net for new fields.

## FoDE alignment

Model for change and correctness; avoid lossy transformations; keep reversible decisions.

## Links

- Design doc: Improved Proposed Schema
- Superseded by: N/A

## References

JSONB indexing guidance; GIN overview.
