"""Test doubles for ports."""

import asyncio
from dataclasses import dataclass, field

from busmora_ai.application.ports.llm import CompletionRequest, CompletionResult


@dataclass
class FakeProbe:
    name: str
    error: Exception | None = None
    delay_seconds: float = 0.0
    calls: int = 0

    async def check(self) -> None:
        self.calls += 1
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        if self.error is not None:
            raise self.error


@dataclass
class FakeLLM:
    """Returns scripted replies in order and records every request."""

    replies: list[str]
    requests: list[CompletionRequest] = field(default_factory=list[CompletionRequest])

    async def complete(self, request: CompletionRequest) -> CompletionResult:
        self.requests.append(request)
        return CompletionResult(
            text=self.replies.pop(0),
            model="fake-model",
            input_tokens=1,
            output_tokens=1,
            cost_micro_usd=0,
        )
