# Updates to port back to busmora-docs

Decisions taken while setting up busmora-ai that the canonical documents in
`busmora-docs` do not reflect yet. This repository does not edit busmora-docs; the
owners of each document should apply these.

## Repository split (ADR 0001)

- [ ] **SYS K-03, SYS ADR-002, D-26, D-51**: replace "two standalone repositories
      (`busmora-backend`, `busmora-frontend`)" with the four repositories
      `busmora-ai`, `busmora-api`, `busmora-web`, `busmora-docs`.
- [ ] **SYS §4.3, §4.9, BTD §2.4, §3.4**: `busmora-workers` (`workers-workflows`,
      `workers-publish`) is built from the `busmora-api` repository.
- [ ] **Backend preference, needs its own decision**: Option B, running
      `workers-workflows` and `workers-publish` on the Temporal **TypeScript** SDK so
      busmora-api stays all TypeScript. If adopted, update SYS §2.4 (the stack table
      lists workers as Python), §4.2 diagram, §4.3, BTD §4 folder tree,
      BTD-ADR-14 (MCP server in TypeScript) and the T06 walking-skeleton description.
- [ ] **BTD scope line and §4 folder tree**: the document covers `busmora-backend`;
      split into a busmora-api design and a busmora-ai design (or point to this repo's
      README and ADRs).
- [ ] **FTD F-9, DS scope line, core/README.md, top-level README "Key Architecture
      Highlights"**: repository names `busmora-frontend` / `busmora-backend`.

## Contracts (ADR 0002)

- [ ] **SYS §6.5, ADR-014, BTD S-10, BTD-ADR-15, BTD §3.4 "Python rules"**: the shared
      `packages/contracts-py` becomes `busmora-ai-contracts`, owned and published by
      busmora-ai at Git tags `contracts-vX.Y.Z`, with JSON Schemas + manifest in
      `contracts/temporal/` and the `ai-http` OpenAPI in `contracts/ai-http/`.
- [ ] If Option B is adopted, Pydantic stays canonical only for payloads busmora-ai
      serves; payloads between api activities and TS workflows become TypeScript-only.
- [ ] **ADR-014 "additive evolution" CI check**: drift check exists; the
      breaking-change check between tags is still to be built.
- [ ] **BTD §3.4**: the Canvas signal envelope and Redis key layout are to be added to
      `busmora-ai-contracts` with the walking skeleton (T06), not yet published.

## Agent step loop (ADR 0003)

- [ ] **SYS §4.6 flow 1, BTD §3.4**: document that `ai.run_agent_step` returns one of
      `continue | needs_crawl | needs_clarification | completed`, and that the workflow
      (not ai-agent) calls `crawl.crawl_sources` and resumes the step.
- [ ] **BTD §11.1 naming example**: activity is `crawl.crawl_sources` (the doc shows
      `crawl.crawl_site`).
- [ ] Recommended timeouts and attempts per activity now live in
      `contracts/temporal/manifest.json` (provisional values from SYS §2.2, §7.3).

## Data access (ADR 0004, 0007)

- [ ] **SYS §2.4, BTD §1 stack, BTD §7.5**: "SQLAlchemy / asyncpg" becomes
      "SQLAlchemy Core / psycopg 3" (single driver, shared with the LangGraph checkpointer).
- [ ] **busmora-api brain module**: publish the real `brain_read.*_v1` view columns and
      the RLS session setting name. busmora-ai's dev stand-in assumes `app.workspace_id`
      and the columns in `deploy/dev-init.sql`.

## Tooling and open decisions

- [ ] **SYS §2.4, BTD §1**: Python 3.11+ becomes Python 3.13 for busmora-ai; uv is the
      package and environment manager.
- [ ] **OD-12 (test frameworks)**, Python side: pytest + pytest-asyncio + temporalio
      testing; ruff (lint/format) and pyright strict.
- [ ] **OD-13 (logs)**, busmora-ai side: structlog JSON with redaction in the logger;
      the central sink and error tracking stay open (T11).
- [ ] **OD-15 (local Temporal)**: Temporal CLI dev server image (`temporalio/temporal`).
- [ ] **OD-16 (CI)**: GitHub Actions with actions pinned by commit SHA; Dependabot.
- [ ] **D-41 (object storage)**: MinIO no longer publishes community images; local
      development uses RustFS. The production vendor is still chosen in T12.
- [ ] **D-31 / R-list**: record the March 2026 LiteLLM PyPI compromise and the
      mitigations in ADR 0005 as a supply-chain risk.

## Planning (`planning/`)

- [ ] **T01, T05, G1-1, OD-17**: "the backend repository" / "both repositories" now
      means busmora-api and busmora-ai separately (plus busmora-web). T01's busmora-ai
      part is this setup; cross-repository local development still needs a written
      procedure.
- [ ] **Health endpoints** for staging (T12): every busmora-ai role serves
      `GET /health/live` and `GET /health/ready`; ports 8100 (ai-http), 8101 (ai-agent),
      8102 (ai-crawl).
