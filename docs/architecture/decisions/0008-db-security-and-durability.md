# ADR 0008 — Database security and durability

**Status:** Accepted  
**Date:** 2025-08-19  

## Context

“Durable” requires encryption at rest, encryption in transit, and recoverability.

## Decision

Use RDS Postgres with KMS encryption at rest, require SSL/TLS for client connections, and enable automated backups / point-in-time restore.

## Options considered

- RDS Postgres with encryption and SSL (chosen)
- Self-managed Postgres (higher ops burden)
- No encryption (not acceptable)

## Consequences

- Encrypted instances, automated backups, and encrypted snapshots.
- Connection string must use SSL, with RDS trust certificates in clients.

## FoDE alignment

Prioritize security; plan for failure; explicit recovery path.

## Links

- Design doc: Durability definition; Cloud & DBMS sections
- Superseded by: N/A

## References

RDS encryption at rest; SSL/TLS to RDS guidance; prescriptive guidance.
