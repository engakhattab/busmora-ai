"""``/health/live`` and ``/health/ready``, shared by all three roles.

- live:  the process is up (no dependency calls); for restart decisions.
- ready: every store this role may use is reachable; 503 otherwise.
"""

from collections.abc import Sequence
from typing import Literal

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from busmora_ai.application.health import DependencyProbe, check_readiness


class LiveResponse(BaseModel):
    status: Literal["live"] = "live"
    role: str
    version: str


class CheckResponse(BaseModel):
    ok: bool
    latency_ms: float
    error: str | None = None


class ReadyResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    role: str
    version: str
    checks: dict[str, CheckResponse]


def build_health_router(
    *,
    role: str,
    version: str,
    probes: Sequence[DependencyProbe],
    timeout_seconds: float,
) -> APIRouter:
    router = APIRouter(prefix="/health", tags=["health"])

    @router.get("/live")
    async def live() -> LiveResponse:  # pyright: ignore[reportUnusedFunction]
        return LiveResponse(role=role, version=version)

    @router.get(
        "/ready",
        responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadyResponse}},
    )
    async def ready(response: Response) -> ReadyResponse:  # pyright: ignore[reportUnusedFunction]
        report = await check_readiness(
            role=role, version=version, probes=probes, timeout_seconds=timeout_seconds
        )
        if not report.ready:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadyResponse(
            status="ready" if report.ready else "not_ready",
            role=report.role,
            version=report.version,
            checks={
                name: CheckResponse(ok=r.ok, latency_ms=r.latency_ms, error=r.error)
                for name, r in report.checks.items()
            },
        )

    return router
