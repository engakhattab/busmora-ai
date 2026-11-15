"""Against the real local stack (deploy/docker-compose.dev.yml) and the repo's .env.

docker compose -f deploy/docker-compose.dev.yml up -d --wait
uv run pytest -m integration
"""

import uuid
from datetime import timedelta

import pytest
from temporalio import workflow
from temporalio.worker import Worker

from busmora_ai.adapters.health.object_storage import ObjectStorageProbe
from busmora_ai.adapters.health.postgres import AI_RUNTIME_SCHEMA, BRAIN_READ_VIEWS, PostgresProbe
from busmora_ai.adapters.health.qdrant import QdrantProbe
from busmora_ai.adapters.health.redis import RedisProbe
from busmora_ai.adapters.health.temporal import TemporalProbe
from busmora_ai.adapters.temporal_client import connect_temporal
from busmora_ai.application.health import check_readiness
from busmora_ai.config.settings import AgentRoleSettings
from busmora_ai.entrypoints.activities.ping import ai_ping
from busmora_ai_contracts import ActivityName, TaskQueue
from busmora_ai_contracts.ping import PingInput, PingOutput

pytestmark = pytest.mark.integration


@pytest.fixture
def settings() -> AgentRoleSettings:
    return AgentRoleSettings()  # pyright: ignore[reportCallIssue]


async def test_ai_agent_reaches_every_allowed_store(settings: AgentRoleSettings) -> None:
    client = await connect_temporal(settings.temporal)
    report = await check_readiness(
        role="ai-agent",
        version="test",
        probes=[
            PostgresProbe(
                settings.postgres.dsn,
                required_relations=BRAIN_READ_VIEWS,
                required_schemas=(AI_RUNTIME_SCHEMA,),
            ),
            QdrantProbe(settings.qdrant.url, api_key=settings.qdrant.api_key),
            RedisProbe(settings.redis.url),
            ObjectStorageProbe(settings.object_storage),
            TemporalProbe(client),
        ],
        timeout_seconds=5,
    )
    assert report.ready, report.checks


@workflow.defn(sandboxed=False)
class CallerWorkflow:
    """Stands in for a busmora-api workflow: calls ai.ping by name, on another queue."""

    @workflow.run
    async def run(self, trace_id: str) -> PingOutput:
        return await workflow.execute_activity(
            ActivityName.AI_PING,
            PingInput(trace_id=trace_id),
            task_queue=TaskQueue.AI_AGENT,
            result_type=PingOutput,
            start_to_close_timeout=timedelta(seconds=10),
        )


async def test_workflow_on_another_queue_calls_ai_ping_by_name(
    settings: AgentRoleSettings,
) -> None:
    client = await connect_temporal(settings.temporal)
    workflow_queue = f"test-workflows-{uuid.uuid4()}"

    async with (
        Worker(client, task_queue=TaskQueue.AI_AGENT, activities=[ai_ping]),
        Worker(client, task_queue=workflow_queue, workflows=[CallerWorkflow]),
    ):
        result = await client.execute_workflow(
            CallerWorkflow.run,
            "trace-integration",
            id=f"test-ping-{uuid.uuid4()}",
            task_queue=workflow_queue,
        )

    assert result.role == "ai-agent"
    assert result.trace_id == "trace-integration"
