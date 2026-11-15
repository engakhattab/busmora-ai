"""Readiness use case: can this role reach every store it is allowed to use?

Probes run concurrently, each with its own timeout. A failure reports only the error
type, never its message, because driver messages can contain hosts or credentials.
"""

import asyncio
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from busmora_ai.observability.logging import get_logger

_log = get_logger(__name__)


class DependencyProbe(Protocol):
    """A port implemented by one adapter per store. ``check`` raises on failure."""

    @property
    def name(self) -> str: ...

    async def check(self) -> None: ...


@dataclass(frozen=True, slots=True)
class ProbeResult:
    ok: bool
    latency_ms: float
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    role: str
    version: str
    checks: dict[str, ProbeResult]

    @property
    def ready(self) -> bool:
        return all(result.ok for result in self.checks.values())


async def _run_probe(probe: DependencyProbe, timeout_seconds: float) -> ProbeResult:
    started = time.perf_counter()
    try:
        await asyncio.wait_for(probe.check(), timeout=timeout_seconds)
    except TimeoutError:
        error = "Timeout"
    except Exception as exc:  # noqa: BLE001 - any failure means "not ready"
        error = type(exc).__name__
    else:
        return ProbeResult(ok=True, latency_ms=_elapsed_ms(started))

    _log.warning("dependency_check_failed", dependency=probe.name, error_type=error)
    return ProbeResult(ok=False, latency_ms=_elapsed_ms(started), error=error)


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 1)


async def check_readiness(
    *,
    role: str,
    version: str,
    probes: Sequence[DependencyProbe],
    timeout_seconds: float,
) -> ReadinessReport:
    results = await asyncio.gather(*(_run_probe(p, timeout_seconds) for p in probes))
    return ReadinessReport(
        role=role,
        version=version,
        checks={probe.name: result for probe, result in zip(probes, results, strict=True)},
    )
