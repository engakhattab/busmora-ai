"""Shared runtime for the Temporal worker roles: one Temporal worker plus a health server.

The worker polls its task queue in the background while uvicorn serves the health
endpoints; stopping uvicorn (SIGINT/SIGTERM) shuts the worker down gracefully.
"""

from collections.abc import Callable, Sequence
from typing import Any

import uvicorn
from temporalio.worker import Worker

from busmora_ai.adapters.health.temporal import TemporalProbe
from busmora_ai.adapters.temporal_client import connect_temporal
from busmora_ai.application.health import DependencyProbe
from busmora_ai.config.settings import ServerSettings, TemporalSettings
from busmora_ai.entrypoints.http.app import create_health_app
from busmora_ai.observability.logging import get_logger

_log = get_logger(__name__)


async def run_worker_role(
    *,
    role: str,
    task_queue: str,
    activities: Sequence[Callable[..., Any]],
    temporal: TemporalSettings,
    health_server: ServerSettings,
    probes: Sequence[DependencyProbe],
    timeout_seconds: float,
) -> None:
    client = await connect_temporal(temporal)
    app = create_health_app(
        role=role, probes=[*probes, TemporalProbe(client)], timeout_seconds=timeout_seconds
    )
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=health_server.host,
            port=health_server.port,
            log_config=None,
            access_log=False,
        )
    )
    worker = Worker(client, task_queue=task_queue, activities=list(activities))

    _log.info("worker_starting", task_queue=task_queue, health_port=health_server.port)
    async with worker:
        await server.serve()
    _log.info("worker_stopped", task_queue=task_queue)
