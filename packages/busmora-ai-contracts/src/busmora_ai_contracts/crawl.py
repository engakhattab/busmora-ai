"""``crawl.crawl_sources``: bounded crawl of permitted public sources (ai-crawl)."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import AnyHttpUrl, AwareDatetime, Field, StringConstraints

from busmora_ai_contracts.base import ContractModel, Sha256Hex, StorageKey, TraceId

CrawlFailureReason = Literal[
    "unreachable",
    "blocked_by_robots",
    "rate_limited",
    "captcha",
    "timeout",
    "unsupported_content",
    "rejected_by_policy",
]
"""Why one target produced no snapshot. ``rejected_by_policy`` covers the SSRF guard."""


class CrawlTarget(ContractModel):
    url: AnyHttpUrl


class CrawlSourcesRequest(ContractModel):
    """What the agent wants crawled. Produced by ``ai.run_agent_step`` (``needs_crawl``)."""

    purpose: Annotated[str, StringConstraints(min_length=1, max_length=500)]
    targets: Annotated[list[CrawlTarget], Field(min_length=1, max_length=20)]
    max_pages_per_target: Annotated[int, Field(ge=1, le=10)] = 3


class CrawlSourcesInput(ContractModel):
    workspace_id: UUID
    task_id: UUID | None = None
    """None for onboarding crawls, which run outside a Task."""
    trace_id: TraceId
    request: CrawlSourcesRequest


class SnapshotRef(ContractModel):
    """A sanitized page snapshot stored in object storage. Content travels by reference."""

    url: AnyHttpUrl
    storage_key: StorageKey
    content_sha256: Sha256Hex
    fetched_at: AwareDatetime


class CrawlFailure(ContractModel):
    url: AnyHttpUrl
    reason: CrawlFailureReason


class CrawlSourcesOutput(ContractModel):
    snapshots: list[SnapshotRef]
    failures: list[CrawlFailure]
