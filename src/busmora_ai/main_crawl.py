"""Entrypoint for role ai-crawl: Temporal activity worker on task queue ``ai-crawl``."""

from busmora_ai.adapters.health.crawler import CrawlerProbe
from busmora_ai.adapters.health.object_storage import ObjectStorageProbe
from busmora_ai.adapters.health.redis import RedisProbe
from busmora_ai.bootstrap.event_loop import run
from busmora_ai.bootstrap.worker_runtime import run_worker_role
from busmora_ai.config.settings import CrawlRoleSettings
from busmora_ai.entrypoints.activities.ping import crawl_ping
from busmora_ai.observability.logging import configure_logging
from busmora_ai_contracts import TaskQueue

ROLE = "ai-crawl"


def main() -> None:
    settings = CrawlRoleSettings()  # pyright: ignore[reportCallIssue]  (values come from env)
    configure_logging(role=ROLE, level=settings.log_level, fmt=settings.log_format)

    run(
        run_worker_role(
            role=ROLE,
            task_queue=TaskQueue.AI_CRAWL,
            activities=[crawl_ping],
            temporal=settings.temporal,
            health_server=settings.health_server,
            probes=[
                RedisProbe(settings.redis.url),
                ObjectStorageProbe(settings.object_storage),
                CrawlerProbe(),
            ],
            timeout_seconds=settings.health_check_timeout_seconds,
        )
    )


if __name__ == "__main__":
    main()
