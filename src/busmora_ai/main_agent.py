"""Entrypoint for role ai-agent: Temporal activity worker on task queue ``ai-agent``."""

from busmora_ai.adapters.health.object_storage import ObjectStorageProbe
from busmora_ai.adapters.health.postgres import AI_RUNTIME_SCHEMA, BRAIN_READ_VIEWS, PostgresProbe
from busmora_ai.adapters.health.qdrant import QdrantProbe
from busmora_ai.adapters.health.redis import RedisProbe
from busmora_ai.bootstrap.event_loop import run
from busmora_ai.bootstrap.worker_runtime import run_worker_role
from busmora_ai.config.settings import AgentRoleSettings
from busmora_ai.entrypoints.activities.ping import ai_ping
from busmora_ai.observability.logging import configure_logging
from busmora_ai_contracts import TaskQueue

ROLE = "ai-agent"


def main() -> None:
    settings = AgentRoleSettings()  # pyright: ignore[reportCallIssue]  (values come from env)
    configure_logging(role=ROLE, level=settings.log_level, fmt=settings.log_format)

    run(
        run_worker_role(
            role=ROLE,
            task_queue=TaskQueue.AI_AGENT,
            activities=[ai_ping],
            temporal=settings.temporal,
            health_server=settings.health_server,
            probes=[
                PostgresProbe(
                    settings.postgres.dsn,
                    required_relations=BRAIN_READ_VIEWS,
                    required_schemas=(AI_RUNTIME_SCHEMA,),
                ),
                QdrantProbe(settings.qdrant.url, api_key=settings.qdrant.api_key),
                RedisProbe(settings.redis.url),
                ObjectStorageProbe(settings.object_storage),
            ],
            timeout_seconds=settings.health_check_timeout_seconds,
        )
    )


if __name__ == "__main__":
    main()
