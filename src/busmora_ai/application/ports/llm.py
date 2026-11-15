"""The only way application and domain code reach a language model.

Concrete gateways (LiteLLM today) live in ``busmora_ai.adapters.llm`` and are the only
modules allowed to import a provider SDK; tests use a fake. See docs/adr/0005.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, Protocol


class ModelTier(StrEnum):
    """Light models route and extract; heavy models plan and write (SYS §4.8)."""

    LIGHT = "light"
    HEAVY = "heavy"


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True, slots=True)
class CompletionRequest:
    tier: ModelTier
    messages: tuple[ChatMessage, ...]
    max_output_tokens: int | None = None
    temperature: float | None = None


@dataclass(frozen=True, slots=True)
class CompletionResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_micro_usd: int | None
    """None when the gateway cannot price the call; usage is still recorded."""


class LLMConfigurationError(Exception):
    """Not retryable: no model for the tier, bad credentials, unknown model."""


class LLMUnavailableError(Exception):
    """Retryable: timeout, rate limit, connection or provider-side failure."""


class LLMPort(Protocol):
    async def complete(self, request: CompletionRequest) -> CompletionResult: ...
