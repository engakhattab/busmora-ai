# contracts/

Generated, committed artifacts that other repositories consume at a Git tag
(`contracts-vX.Y.Z`). **Do not edit by hand.** Regenerate with:

```bash
uv run python scripts/export_contracts.py
```

CI runs the same script with `--check` and fails if these files are stale.

| Path | Consumer | Use |
|---|---|---|
| `temporal/manifest.json` | busmora-api workflows | Task queues, activity names, recommended timeouts/attempts, non-retryable error types |
| `temporal/*.input.json`, `temporal/*.output.json` | busmora-api workflows | JSON Schema per activity: generate TS types, validate with Ajv |
| `ai-http/openapi.json` | busmora-api `ai-gateway` | Generate the typed `ai-http` client |

Activities marked `"status": "planned"` have a published contract but no worker
registers them yet.
