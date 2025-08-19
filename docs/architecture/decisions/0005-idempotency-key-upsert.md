# ADR 0005 — Idempotency and primary key strategy

**Status:** Accepted  
**Date:** 2025-08-19  

## Context

The job feed is re-fetched daily; postings may be updated. We need safe re-runs without duplicates.

## Decision

Use a stable natural key (prefer `MatchedObjectId`; fallback to a composite like `PositionID` + `PositionURI` if necessary). Upsert with `INSERT ... ON CONFLICT DO UPDATE`.

## Options considered

- Surrogate autoincrement ID only
- Natural key with upsert (chosen)
- Full “slowly changing” history (out of scope for now)

## Consequences

- Safe re-ingest and update of fields.
- Track `created_at` / `last_seen_at` / `ingest_run_id` for lineage.
- Add history tables later if needed.

## FoDE alignment

Plan for failure and recovery; clear lineage; correctness over convenience.

## Links

- Design doc: Schema and ingestion strategy
- Superseded by: N/A

## References

Postgres ON CONFLICT docs; upsert overview.
