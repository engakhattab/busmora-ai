---
status: accepted
date: 2026-11-15
---

# ai.run_agent_step is a step loop with a discriminated outcome

A Temporal activity cannot schedule another activity, and the workflow (owned by busmora-api) must stay the only orchestrator. So `ai.run_agent_step` runs the LangGraph graph for one bounded step and returns exactly one `outcome`: `continue` (call again), `needs_crawl` (the workflow runs `crawl.crawl_sources` on the `ai-crawl` queue and resumes with `crawl_results`), `needs_clarification` (the workflow opens the clarification, waits up to 7 days and resumes with `clarification_answered`), or `completed` (the workflow persists the result through platform activities). We rejected letting ai-agent call Scrapling in-process, because that would merge agent work and crawling into one process and remove the separation of untrusted crawled content (SYS §4.7).

## Consequences

- `task_id` is the LangGraph thread id, so a retried or resumed step continues from its checkpoint; the step must be idempotent.
- Every outcome carries the step's usage so platform activities can record it (NFR-06, FR-27).
- `completed` returns a reference to the result in object storage, not the result inline. The result's typed schema is added when the first result-producing feature lands (T25/T29).
