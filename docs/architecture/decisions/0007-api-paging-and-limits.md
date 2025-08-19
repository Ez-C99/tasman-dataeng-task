# ADR 0007 — API paging and limits

**Status:** Accepted  
**Date:** 2025-08-19  

## Context

USAJOBS Search caps at 10,000 rows per query and 500 rows per page. Public jobs are returned by default.

## Decision

Use `ResultsPerPage=500` and sequential paging with exponential backoff on 429/5xx. Prefer API-side filtering (e.g., `LocationName` + `Radius`) to reduce payload and cost.

## Options considered

- Sequential paging (chosen)
- Bounded concurrency (future optimization)
- Client-side geo-filtering only (deprioritized)

## Consequences

- Simple, rate-friendly extraction; robust to transient failures.
- Concurrency can be introduced later behind a throttle.

## FoDE alignment

Keep systems simple; measure before optimizing; minimize data gravity early.

## Links

- Design doc: API & Chicago filtering
- Superseded by: N/A

## References

USAJOBS pagination & limits; auth header requirements.
