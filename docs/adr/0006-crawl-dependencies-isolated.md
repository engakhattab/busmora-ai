---
status: accepted
date: 2026-11-15
---

# Crawling dependencies live in an optional extra and their own image

Scrapling's browser fetchers bring Playwright, browsers and system libraries that only `ai-crawl` needs. They are declared as the optional `crawl` extra (`uv sync --extra crawl`), imported only under `adapters/crawler/`, and installed only in the `ai-crawl` target of `deploy/Dockerfile`. The `ai-http` and `ai-agent` images stay small, and the processes that handle LLM provider keys never ship a browser that renders untrusted pages.
