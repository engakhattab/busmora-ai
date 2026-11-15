"""``ai.ping`` / ``crawl.ping``: liveness of a worker pool, used by the walking skeleton."""

from busmora_ai_contracts.base import ContractModel, TraceId


class PingInput(ContractModel):
    trace_id: TraceId


class PingOutput(ContractModel):
    role: str
    service_version: str
    contracts_version: str
    trace_id: TraceId
