## What and why

<!-- One or two sentences. Link the task (e.g. P1-E01-T01) and any ADR. -->

## Checklist

- [ ] `uv run ruff format --check && uv run ruff check && uv run pyright && uv run pytest` pass
- [ ] If a contract changed: it is additive, `scripts/export_contracts.py` was run, and `contracts/` is committed
- [ ] No secret, credential or real customer data in code, tests or logs
- [ ] A teammate reviewed the change and witnessed the completion evidence (Definition of Done 6)
