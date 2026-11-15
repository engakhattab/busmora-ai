"""FastAPI applications: the ai-http service and the health servers of the worker roles."""

from collections.abc import Sequence

from fastapi import FastAPI

from busmora_ai import __version__
from busmora_ai.application.health import DependencyProbe
from busmora_ai.entrypoints.http.health import build_health_router

AI_HTTP_ROLE = "ai-http"


def create_http_app(
    *,
    probes: Sequence[DependencyProbe],
    timeout_seconds: float,
    expose_docs: bool = False,
) -> FastAPI:
    """ai-http. Internal only (no public ingress). Route-and-reply and Brain retrieval
    routes arrive with their features (T18, T24), behind service-JWT verification."""
    app = FastAPI(
        title="busmora-ai ai-http",
        version=__version__,
        description="Internal AI service for busmora-api: quick replies and Brain retrieval.",
        docs_url="/docs" if expose_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if expose_docs else None,
    )
    app.include_router(
        build_health_router(
            role=AI_HTTP_ROLE, version=__version__, probes=probes, timeout_seconds=timeout_seconds
        )
    )
    return app


def create_health_app(
    *, role: str, probes: Sequence[DependencyProbe], timeout_seconds: float
) -> FastAPI:
    """Health endpoints for a Temporal worker role (ai-agent, ai-crawl)."""
    app = FastAPI(
        title=f"busmora-ai {role} health",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.include_router(
        build_health_router(
            role=role, version=__version__, probes=probes, timeout_seconds=timeout_seconds
        )
    )
    return app
