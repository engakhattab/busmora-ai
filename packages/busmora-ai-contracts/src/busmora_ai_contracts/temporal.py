"""Temporal routing: task queues, activity names, recommended call options and errors.

Workflows in busmora-api call these activities **by name** on these task queues.
The recommended timeouts and attempts are provisional engineering values (SYS §2.2,
§7.3) that the caller sets on its RetryPolicy; revise them from measurements.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal

from busmora_ai_contracts.agent_step import RunAgentStepInput, RunAgentStepOutput
from busmora_ai_contracts.crawl import CrawlSourcesInput, CrawlSourcesOutput
from busmora_ai_contracts.ping import PingInput, PingOutput


class TaskQueue(StrEnum):
    AI_AGENT = "ai-agent"
    AI_CRAWL = "ai-crawl"


class ActivityName(StrEnum):
    AI_PING = "ai.ping"
    AI_RUN_AGENT_STEP = "ai.run_agent_step"
    CRAWL_PING = "crawl.ping"
    CRAWL_CRAWL_SOURCES = "crawl.crawl_sources"


class NonRetryableErrorType(StrEnum):
    """``ApplicationError.type`` values that mean "do not retry". Anything else raised by
    a busmora-ai activity is an infrastructure failure and may be retried."""

    INVALID_INPUT = "ai.invalid_input"
    CONFIGURATION_ERROR = "ai.configuration_error"
    BUDGET_EXHAUSTED = "ai.budget_exhausted"
    POLICY_VIOLATION = "ai.policy_violation"


ActivityStatus = Literal["available", "planned"]


@dataclass(frozen=True, slots=True)
class ActivitySpec:
    name: ActivityName
    task_queue: TaskQueue
    input_type: Any
    output_type: Any
    status: ActivityStatus
    """``planned``: the contract is published but no worker registers it yet."""
    start_to_close_seconds: int
    heartbeat_seconds: int | None
    max_attempts: int


ACTIVITIES: tuple[ActivitySpec, ...] = (
    ActivitySpec(
        name=ActivityName.AI_PING,
        task_queue=TaskQueue.AI_AGENT,
        input_type=PingInput,
        output_type=PingOutput,
        status="available",
        start_to_close_seconds=10,
        heartbeat_seconds=None,
        max_attempts=3,
    ),
    ActivitySpec(
        name=ActivityName.CRAWL_PING,
        task_queue=TaskQueue.AI_CRAWL,
        input_type=PingInput,
        output_type=PingOutput,
        status="available",
        start_to_close_seconds=10,
        heartbeat_seconds=None,
        max_attempts=3,
    ),
    ActivitySpec(
        name=ActivityName.AI_RUN_AGENT_STEP,
        task_queue=TaskQueue.AI_AGENT,
        input_type=RunAgentStepInput,
        output_type=RunAgentStepOutput,
        status="planned",
        # A step stops at its own budget; up to three attempts (SYS §7.3).
        start_to_close_seconds=600,
        heartbeat_seconds=30,
        max_attempts=3,
    ),
    ActivitySpec(
        name=ActivityName.CRAWL_CRAWL_SOURCES,
        task_queue=TaskQueue.AI_CRAWL,
        input_type=CrawlSourcesInput,
        output_type=CrawlSourcesOutput,
        status="planned",
        # Research and crawl <= 5 min; unreachable site -> 2 retries (SYS §2.2, §7.3).
        start_to_close_seconds=300,
        heartbeat_seconds=30,
        max_attempts=3,
    ),
)
