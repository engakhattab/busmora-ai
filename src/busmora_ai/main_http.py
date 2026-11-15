"""Entrypoint for role ai-http: internal FastAPI (quick replies, Brain retrieval)."""

import uvicorn

from busmora_ai.adapters.health.postgres import BRAIN_READ_VIEWS, PostgresProbe
from busmora_ai.adapters.health.qdrant import QdrantProbe
from busmora_ai.bootstrap.event_loop import run
from busmora_ai.config.settings import HttpRoleSettings
from busmora_ai.entrypoints.http.app import AI_HTTP_ROLE, create_http_app
from busmora_ai.observability.logging import configure_logging


def main() -> None:
    settings = HttpRoleSettings()  # pyright: ignore[reportCallIssue]  (values come from env)
    configure_logging(role=AI_HTTP_ROLE, level=settings.log_level, fmt=settings.log_format)

    app = create_http_app(
        probes=[
            PostgresProbe(settings.postgres.dsn, required_relations=BRAIN_READ_VIEWS),
            QdrantProbe(settings.qdrant.url, api_key=settings.qdrant.api_key),
        ],
        timeout_seconds=settings.health_check_timeout_seconds,
        expose_docs=settings.environment == "local",
    )
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=settings.server.host,
            port=settings.server.port,
            log_config=None,
        )
    )
    run(server.serve())


if __name__ == "__main__":
    main()
