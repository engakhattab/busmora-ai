"""``ai.run_agent_step``: one bounded step of the Director's LangGraph run (ai-agent).

The workflow (owned by busmora-api) loops on this activity. Each step runs the graph
until it finishes, needs something only the workflow can provide, or exhausts its
step budget, and returns exactly one outcome:

- ``continue``             -> call ``run_agent_step`` again with the next step number
- ``needs_crawl``          -> run ``crawl.crawl_sources``, then resume with ``crawl_results``
- ``needs_clarification``  -> open the clarification, wait for the owner's answer
                              (up to 7 days), then resume with ``clarification_answered``
- ``completed``            -> persist the result through the platform activities

ai-agent never calls another activity itself. See docs/adr/0003.
"""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints

from busmora_ai_contracts.base import ContractModel, Sha256Hex, StorageKey, TraceId
from busmora_ai_contracts.crawl import CrawlSourcesOutput, CrawlSourcesRequest

ShortId = Annotated[str, StringConstraints(min_length=1, max_length=64)]

# ---------------------------------------------------------------- input


class CrawlResultsResume(ContractModel):
    kind: Literal["crawl_results"] = "crawl_results"
    crawl: CrawlSourcesOutput


class ClarificationAnswer(ContractModel):
    question_id: ShortId
    selected_option_ids: list[ShortId] = Field(default_factory=list[ShortId])
    custom_answer: Annotated[str, StringConstraints(max_length=2000)] | None = None


class ClarificationAnsweredResume(ContractModel):
    kind: Literal["clarification_answered"] = "clarification_answered"
    answers: Annotated[list[ClarificationAnswer], Field(min_length=1)]


StepResume = Annotated[
    CrawlResultsResume | ClarificationAnsweredResume,
    Field(discriminator="kind"),
]


class RunAgentStepInput(ContractModel):
    workspace_id: UUID
    task_id: UUID
    """Also the LangGraph thread id, so a retried step resumes from its checkpoint."""
    trace_id: TraceId
    step_number: Annotated[int, Field(ge=1)]
    resume: StepResume | None = None
    """What the workflow obtained for the previous step's request, if anything."""


# ---------------------------------------------------------------- output


class LlmUsage(ContractModel):
    model: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    input_tokens: Annotated[int, Field(ge=0)]
    output_tokens: Annotated[int, Field(ge=0)]
    cost_micro_usd: Annotated[int, Field(ge=0)] | None = None
    """Cost in millionths of a US dollar; None when the provider price is unknown."""


class StepUsage(ContractModel):
    """Usage consumed during this step, for platform.record_progress (NFR-06, FR-27)."""

    llm_calls: list[LlmUsage] = Field(default_factory=list[LlmUsage])


class ClarificationOption(ContractModel):
    option_id: ShortId
    label: Annotated[str, StringConstraints(min_length=1, max_length=300)]


class ClarificationQuestion(ContractModel):
    question_id: ShortId
    prompt: Annotated[str, StringConstraints(min_length=1, max_length=1000)]
    selection: Literal["single", "multiple"]
    options: Annotated[list[ClarificationOption], Field(min_length=1, max_length=8)]
    allow_custom_answer: bool = True


class ClarificationForm(ContractModel):
    """Choice-first clarification (FR-18), rendered by the web app."""

    questions: Annotated[list[ClarificationQuestion], Field(min_length=1, max_length=5)]


class ResultRef(ContractModel):
    """The typed Task result, stored in object storage. Its schema is defined by the
    feature that first produces results (T25/T29) and added here additively."""

    storage_key: StorageKey
    content_sha256: Sha256Hex
    media_type: Literal["application/json"] = "application/json"


class StepContinue(ContractModel):
    outcome: Literal["continue"] = "continue"
    step_number: int
    usage: StepUsage = StepUsage()


class StepNeedsCrawl(ContractModel):
    outcome: Literal["needs_crawl"] = "needs_crawl"
    step_number: int
    usage: StepUsage = StepUsage()
    request: CrawlSourcesRequest


class StepNeedsClarification(ContractModel):
    outcome: Literal["needs_clarification"] = "needs_clarification"
    step_number: int
    usage: StepUsage = StepUsage()
    form: ClarificationForm


class StepCompleted(ContractModel):
    outcome: Literal["completed"] = "completed"
    step_number: int
    usage: StepUsage = StepUsage()
    status: Literal["completed", "partially_completed"]
    """``partially_completed`` when time, cost or evidence limits ended the work early."""
    result: ResultRef


RunAgentStepOutput = Annotated[
    StepContinue | StepNeedsCrawl | StepNeedsClarification | StepCompleted,
    Field(discriminator="outcome"),
]
