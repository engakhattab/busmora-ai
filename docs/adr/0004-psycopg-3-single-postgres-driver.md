---
status: accepted
date: 2026-11-15
---

# psycopg 3 is the only Postgres driver

The backend design names SQLAlchemy Core with asyncpg for the read views (BTD §7.5), but `langgraph-checkpoint-postgres` requires psycopg 3. Using psycopg 3 for both the checkpointer and SQLAlchemy Core (its `postgresql+psycopg` dialect) gives one driver to configure, pool, patch and debug instead of two. asyncpg's speed advantage does not matter for read-only retrieval queries at Busmora's scale.

## Consequences

- On Windows, psycopg's async mode cannot use the default Proactor event loop, so local runs use the selector loop (`bootstrap/event_loop.py`, `tests/conftest.py`). Linux containers are unaffected.
