# busmora-ai

Stateless AI compute for **Busmora**, the Arabic-first AI Marketing Director. This
repository holds the three process roles of the `busmora-ai` deployable:

| Role | What it does | Reached by | Health |
|---|---|---|---|
| `ai-http` | Fast Router and quick replies; read-only Brain retrieval | Internal HTTP from busmora-api (service JWT) | `:8100/health/*` |
| `ai-agent` | Director graph (Router, Orchestrator, specialists), extraction, embeddings and indexing, content, KPIs | Temporal task queue `ai-agent` | `:8101/health/*` |
| `ai-crawl` | Bounded crawling with Scrapling, sanitization, crawl cache | Temporal task queue `ai-crawl` | `:8102/health/*` |

**Boundaries.** busmora-ai never writes domain tables, owns no migrations, defines no
Temporal workflows and never handles publishing credentials. Those belong to
busmora-api. See [ADR 0001](docs/adr/0001-repository-scope-and-four-repo-split.md).
The product and system design live in the `busmora-docs` repository; changes this
repo needs there are listed in [docs/busmora-docs-updates.md](docs/busmora-docs-updates.md).

> **Status:** foundation only. Each role starts, answers health checks and (for the
> workers) serves a `ping` activity. No AI feature is implemented yet.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) 0.13.8 or newer. uv manages Python 3.13, the
  virtual environment and all dependencies. **Do not use pip.**
- Docker with Compose v2 (Docker Desktop on Windows/macOS) for the local stack.
- Git.

## Quick start

```bash
uv sync                         # creates .venv with Python 3.13 and all dev tools
cp .env.example .env            # local settings matching the compose stack
docker compose -f deploy/docker-compose.dev.yml up -d --wait
```

Run each role in its own terminal:

```bash
uv run busmora-ai-http
uv run busmora-ai-agent
uv run --extra crawl busmora-ai-crawl     # needs the crawl extra, see below
```

Then check readiness, for example `curl http://127.0.0.1:8101/health/ready`. A role
returns `200` with `"status": "ready"` when it reaches every store it is allowed to
use, otherwise `503` with the failing check named (error type only, never the message).

Local services: Temporal UI at http://127.0.0.1:8233, RustFS console at
http://127.0.0.1:9001, Qdrant dashboard at http://127.0.0.1:6333/dashboard.

### Crawling (ai-crawl)

Browser crawling is an optional extra so the other roles stay light
([ADR 0006](docs/adr/0006-crawl-dependencies-isolated.md)):

```bash
uv sync --extra crawl
uv run scrapling install        # downloads browsers and their system dependencies
```

Without it, `ai-crawl` still starts but reports `crawler` as not ready.

## Everyday commands

| Task | Command |
|---|---|
| Install / update the environment | `uv sync` |
| Add a runtime dependency | `uv add <package>` |
| Add a dev tool | `uv add --dev <package>` |
| Format | `uv run ruff format` |
| Lint | `uv run ruff check` (`--fix` to apply fixes) |
| Type-check (strict) | `uv run pyright` |
| Unit tests | `uv run pytest` |
| Integration tests (stack running) | `uv run pytest -m integration` |
| Regenerate contracts | `uv run python scripts/export_contracts.py` |
| Check contracts are current | `uv run python scripts/export_contracts.py --check` |
| Git hooks (optional) | `uvx pre-commit install` |

CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) runs the same checks, the
integration tests against the compose stack, and builds all three images.

## Configuration

Settings are typed per role in [`config/settings.py`](src/busmora_ai/config/settings.py)
and validated at startup; a missing or invalid value stops the process. Variables use
the prefix `BUSMORA_AI_` and `__` for nesting (`BUSMORA_AI_POSTGRES__DSN`). Each role
declares only the stores it may use, so `ai-crawl` cannot be given database settings.

Locally, values come from `.env` (git-ignored). In real environments they come from
the secrets store (OD-5), never from a committed file.

## Layout

```
packages/busmora-ai-contracts/   Published contract: activity names, queues, payload models
src/busmora_ai/
  main_http.py | main_agent.py | main_crawl.py    composition roots, one per role
  bootstrap/        event loop and worker runtime (wiring only)
  entrypoints/      FastAPI routes and Temporal activities; no logic
  application/      use cases and the ports they declare (e.g. LLMPort)
  adapters/         implementations of ports: stores, LiteLLM, Temporal client
  config/           typed settings per role
  observability/    structured logging with redaction
contracts/          generated JSON Schemas + OpenAPI (committed, checked in CI)
deploy/             Dockerfile (3 targets), dev compose stack, dev SQL bootstrap
scripts/            contract export and drift check
docs/adr/           decisions specific to this repository
tests/              unit, architecture and integration tests
```

`domain/` (graph, retrieval, content rules) is added with the first feature. The
dependency rule is enforced by `tests/architecture/test_import_boundaries.py`:
`application` and `domain` never import adapters or entrypoints, `entrypoints` never
import adapters, and each SDK (litellm, scrapling, psycopg, boto3, …) is imported only
by its own adapter.

## Contracts with other repositories

busmora-ai owns and publishes its contracts
([ADR 0002](docs/adr/0002-contracts-owned-and-published-by-busmora-ai.md)):

- `contracts/temporal/manifest.json`: task queues, activity names, recommended timeouts
  and attempts, and the `ApplicationError` types that must not be retried.
- `contracts/temporal/<activity>.{input,output}.json`: JSON Schema for each payload.
- `contracts/ai-http/openapi.json`: the internal HTTP API.

To release a version: bump `version` in `packages/busmora-ai-contracts/pyproject.toml`,
regenerate, merge, then tag `contracts-vX.Y.Z`. Changes must be additive; see the
package [README](packages/busmora-ai-contracts/README.md).

`ai.run_agent_step` is a step loop whose output is `continue | needs_crawl |
needs_clarification | completed`; the busmora-api workflow orchestrates crawling and
clarification ([ADR 0003](docs/adr/0003-run-agent-step-step-loop-contract.md)).

## Local database

busmora-api owns all migrations. Until its migrations exist, the compose Postgres runs
[`deploy/dev-init.sql`](deploy/dev-init.sql) on first start: a read-only `busmora_ai`
role, the `ai_runtime` schema and stand-in `brain_read` views with workspace
row-level security ([ADR 0007](docs/adr/0007-dev-database-bootstrap.md)). Their
columns are provisional. Re-create the database with
`docker compose -f deploy/docker-compose.dev.yml down -v`.

## Docker images

```bash
docker build -f deploy/Dockerfile --target ai-http  -t busmora-ai-http  .
docker build -f deploy/Dockerfile --target ai-agent -t busmora-ai-agent .
docker build -f deploy/Dockerfile --target ai-crawl -t busmora-ai-crawl .
```

Images run as a non-root user, install only from `uv.lock`, and listen on 8100, 8101
and 8102 respectively.

## Git workflow

- `main` is protected; work on short-lived branches and merge by pull request with one
  reviewer (Definition of Done item 6), squash-merged.
- Conventional commit messages (`feat(agent): …`, `fix(crawl): …`, `docs(adr): …`).
- Commit `uv.lock` and regenerated `contracts/` with the change that caused them.

## Windows notes

- Line endings are normalized to LF by `.gitattributes`.
- psycopg's async driver needs the selector event loop on Windows; the entrypoints and
  tests select it automatically ([ADR 0004](docs/adr/0004-psycopg-3-single-postgres-driver.md)).
