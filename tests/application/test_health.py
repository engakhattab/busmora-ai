from busmora_ai.application.health import check_readiness
from tests.fakes import FakeProbe


async def test_ready_when_every_probe_passes() -> None:
    report = await check_readiness(
        role="ai-agent",
        version="0.1.0",
        probes=[FakeProbe("postgres"), FakeProbe("redis")],
        timeout_seconds=1,
    )
    assert report.ready
    assert set(report.checks) == {"postgres", "redis"}


async def test_not_ready_reports_only_the_error_type() -> None:
    leaky_driver_message = "connection to postgresql://user:hunter2@db failed"
    report = await check_readiness(
        role="ai-http",
        version="0.1.0",
        probes=[
            FakeProbe("postgres", error=ConnectionError(leaky_driver_message)),
            FakeProbe("qdrant"),
        ],
        timeout_seconds=1,
    )
    assert not report.ready
    assert report.checks["postgres"].error == "ConnectionError"
    assert report.checks["qdrant"].ok


async def test_slow_probe_times_out() -> None:
    report = await check_readiness(
        role="ai-crawl",
        version="0.1.0",
        probes=[FakeProbe("redis", delay_seconds=1)],
        timeout_seconds=0.05,
    )
    assert report.checks["redis"].error == "Timeout"
    assert not report.ready


async def test_no_probes_means_ready() -> None:
    report = await check_readiness(role="x", version="0", probes=[], timeout_seconds=1)
    assert report.ready
