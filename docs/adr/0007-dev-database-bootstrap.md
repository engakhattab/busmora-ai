---
status: accepted
date: 2026-11-15
---

# A dev-only SQL bootstrap stands in for busmora-api migrations

busmora-api owns every migration, including the `brain_read` views and the `ai_runtime` schema (SYS ADR-008, BTD-ADR-09). So that busmora-ai is not blocked while those migrations are being written, `deploy/dev-init.sql` creates them in the local compose Postgres only: a read-only `busmora_ai` role, the `ai_runtime` schema it owns, stand-in base tables, workspace row-level security forced on the views' owner, and the three `*_v1` eligibility views.

## Consequences

- The view columns and the RLS session setting (`app.workspace_id`) are **provisional guesses**. When busmora-api publishes the real view contract, update the adapters, then replace this file with the api's migrations.
- The file runs only when the Postgres volume is empty; recreate it with `docker compose ... down -v`.
