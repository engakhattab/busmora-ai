# busmora-ai-contracts

The canonical, versioned contract for everything `busmora-ai` serves over Temporal:
task queue names, activity names, input/output models, recommended timeouts and
non-retryable error types.

- **Python consumers** depend on this package by Git tag (`contracts-vX.Y.Z`).
- **TypeScript consumers** (`busmora-api` workflows) use the JSON Schemas and
  `manifest.json` exported to `contracts/temporal/` at the same tag. Generate TS types
  from the schemas and validate payloads at runtime with Ajv.

Rules (see `docs/adr/0002` and `docs/adr/0003`):

1. Changes are **additive only**: new optional fields, new variants, new activities.
   Never remove or retype a field in place; publish `..._v2` next to the old one.
2. Models ignore unknown fields, so an older worker keeps accepting payloads from a
   newer caller.
3. Never hand-edit `contracts/`; regenerate with `uv run python scripts/export_contracts.py`.
