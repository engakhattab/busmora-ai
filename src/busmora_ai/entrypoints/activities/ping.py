"""``ai.ping`` and ``crawl.ping``: prove a workflow can reach each worker pool by name."""

from temporalio import activity

from busmora_ai import __version__
from busmora_ai_contracts import ActivityName
from busmora_ai_contracts import __version__ as contracts_version
from busmora_ai_contracts.ping import PingInput, PingOutput


def _pong(role: str, payload: PingInput) -> PingOutput:
    return PingOutput(
        role=role,
        service_version=__version__,
        contracts_version=contracts_version,
        trace_id=payload.trace_id,
    )


@activity.defn(name=ActivityName.AI_PING)
async def ai_ping(payload: PingInput) -> PingOutput:
    return _pong("ai-agent", payload)


@activity.defn(name=ActivityName.CRAWL_PING)
async def crawl_ping(payload: PingInput) -> PingOutput:
    return _pong("ai-crawl", payload)
