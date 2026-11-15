---
status: accepted
date: 2026-11-15
---

# busmora-ai holds only the three AI process roles

Busmora is split into four repositories (`busmora-ai`, `busmora-api`, `busmora-web`, `busmora-docs`), replacing the two-repository layout in SYS ADR-002 / K-03 and decisions D-26 / D-51. This repository contains exactly the `ai-http`, `ai-agent` and `ai-crawl` roles of the `busmora-ai` deployable: Router and quick replies, Brain retrieval, the Director's agents and specialists, extraction, embeddings and indexing, content drafting, deterministic KPIs and crawling. The `busmora-workers` deployable (workflow definitions and the publish worker with MCP tools and KMS decryption) belongs to `busmora-api`; the backend team favours running it on the Temporal TypeScript SDK so that repository stays all TypeScript.

The reason for the boundary: workflows only sequence the api's own rules (BTD-ADR-10), and keeping publishing and credentials out of this repository makes "no AI in the publishing path after Approval" (SYS ADR-005) structural, not a convention.

## Consequences

- busmora-ai never writes domain tables, owns no migrations, defines no workflows and never handles platform credentials.
- The two repositories meet only through published contracts: Temporal activity names, task queues and payload schemas, the `ai-http` OpenAPI, and the api-owned `brain_read` views (see 0002).
