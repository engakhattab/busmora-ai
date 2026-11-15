from uuid import uuid4

import pytest
from pydantic import TypeAdapter, ValidationError

from busmora_ai_contracts.agent_step import (
    RunAgentStepInput,
    RunAgentStepOutput,
    StepCompleted,
    StepContinue,
    StepNeedsClarification,
    StepNeedsCrawl,
)

OUTPUT = TypeAdapter[StepContinue | StepNeedsCrawl | StepNeedsClarification | StepCompleted](
    RunAgentStepOutput
)

SHA = "a" * 64


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"outcome": "continue", "step_number": 1}, StepContinue),
        (
            {
                "outcome": "needs_crawl",
                "step_number": 2,
                "request": {
                    "purpose": "competitor pricing",
                    "targets": [{"url": "https://example.com"}],
                },
            },
            StepNeedsCrawl,
        ),
        (
            {
                "outcome": "needs_clarification",
                "step_number": 3,
                "form": {
                    "questions": [
                        {
                            "question_id": "discount",
                            "prompt": "Is there a Ramadan discount?",
                            "selection": "single",
                            "options": [{"option_id": "yes", "label": "Yes"}],
                        }
                    ]
                },
            },
            StepNeedsClarification,
        ),
        (
            {
                "outcome": "completed",
                "step_number": 4,
                "status": "completed",
                "result": {"storage_key": "ws/results/r.json", "content_sha256": SHA},
            },
            StepCompleted,
        ),
    ],
)
def test_output_union_selects_variant_by_outcome(
    payload: dict[str, object], expected: type
) -> None:
    assert isinstance(OUTPUT.validate_python(payload), expected)


def test_output_rejects_unknown_outcome() -> None:
    with pytest.raises(ValidationError):
        OUTPUT.validate_python({"outcome": "publish_now", "step_number": 1})


def test_output_round_trips_through_json() -> None:
    original = StepNeedsCrawl.model_validate(
        {
            "step_number": 2,
            "request": {"purpose": "p", "targets": [{"url": "https://example.com/a"}]},
        }
    )
    assert OUTPUT.validate_json(OUTPUT.dump_json(original)) == original


def test_input_ignores_unknown_fields_for_additive_evolution() -> None:
    parsed = RunAgentStepInput.model_validate(
        {
            "workspace_id": str(uuid4()),
            "task_id": str(uuid4()),
            "trace_id": "t-1",
            "step_number": 1,
            "field_added_in_a_later_version": True,
        }
    )
    assert parsed.resume is None


def test_input_resume_is_discriminated_by_kind() -> None:
    parsed = RunAgentStepInput.model_validate(
        {
            "workspace_id": str(uuid4()),
            "task_id": str(uuid4()),
            "trace_id": "t-1",
            "step_number": 5,
            "resume": {
                "kind": "clarification_answered",
                "answers": [{"question_id": "discount", "selected_option_ids": ["yes"]}],
            },
        }
    )
    assert parsed.resume is not None
    assert parsed.resume.kind == "clarification_answered"


def test_crawl_request_is_bounded() -> None:
    with pytest.raises(ValidationError):
        StepNeedsCrawl.model_validate(
            {
                "step_number": 1,
                "request": {
                    "purpose": "p",
                    "targets": [{"url": "https://example.com"}],
                    "max_pages_per_target": 50,
                },
            }
        )
