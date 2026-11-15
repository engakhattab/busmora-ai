---
status: accepted
date: 2026-11-15
---

# LiteLLM SDK behind LLMPort, with supply-chain hardening

We keep LiteLLM as the model gateway (D-31) so the provider bake-off (T08) can change models without code changes, but use only its SDK, never its proxy server. On 24 March 2026 LiteLLM 1.82.7 and 1.82.8 were published to PyPI with credential-stealing code, after the project's CI used an unpinned, compromised scanner. We therefore require `litellm>=1.83.0,<2`, install only from the hashed `uv.lock` (`uv sync --locked`), pin CI actions by commit SHA, and update through reviewed Dependabot pull requests.

All model access goes through `application/ports/llm.py` (`LLMPort`). `busmora_ai.adapters.llm` is the only package allowed to import `litellm`, enforced by `tests/architecture/test_import_boundaries.py`, so replacing LiteLLM with direct provider SDKs is a one-adapter change.
