---
status: accepted
date: 2026-11-15
---

# busmora-ai owns and publishes its contracts by Git tag

With separate repositories the shared `packages/contracts-py` of BTD-ADR-15 can no longer be shared in-tree, so each provider owns its contract. busmora-ai publishes the `busmora-ai-contracts` package (Pydantic models, task queues, activity names, recommended call options, non-retryable error types) and exports its JSON Schemas, a manifest and the `ai-http` OpenAPI into the committed `contracts/` folder. A release is a Git tag `contracts-vX.Y.Z`: Python consumers depend on the package at that tag; busmora-api generates TypeScript types and Ajv validators from the schemas at that tag. CI runs `scripts/export_contracts.py --check` and fails on drift. We chose tags over a private package registry because it needs no extra infrastructure.

## Consequences

- Evolution is additive only: models ignore unknown fields, new fields are optional, and breaking changes ship as a new activity or `_v2` model next to the old one, because month-long workflows may replay old payloads.
- Not done yet: an automated breaking-change check (field removed or retyped) between the previous tag and HEAD. Until then, contract changes are reviewed by hand.
