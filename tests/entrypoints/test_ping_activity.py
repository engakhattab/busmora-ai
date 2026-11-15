from temporalio.testing import ActivityEnvironment

from busmora_ai import __version__
from busmora_ai.entrypoints.activities.ping import ai_ping, crawl_ping
from busmora_ai_contracts import __version__ as contracts_version
from busmora_ai_contracts.ping import PingInput, PingOutput


async def test_ai_ping_echoes_trace_and_versions() -> None:
    result: PingOutput = await ActivityEnvironment().run(ai_ping, PingInput(trace_id="t-42"))

    assert result == PingOutput(
        role="ai-agent",
        service_version=__version__,
        contracts_version=contracts_version,
        trace_id="t-42",
    )


async def test_crawl_ping_identifies_its_role() -> None:
    result: PingOutput = await ActivityEnvironment().run(crawl_ping, PingInput(trace_id="t-1"))

    assert result.role == "ai-crawl"
