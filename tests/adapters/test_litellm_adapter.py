from functools import partial
from typing import Any

import litellm
import pytest

from busmora_ai.adapters.llm.litellm_adapter import LiteLLMAdapter
from busmora_ai.application.ports.llm import (
    ChatMessage,
    CompletionRequest,
    LLMConfigurationError,
    LLMPort,
    LLMUnavailableError,
    ModelTier,
)

REQUEST = CompletionRequest(
    tier=ModelTier.LIGHT, messages=(ChatMessage(role="user", content="مرحبا"),)
)


async def test_returns_text_and_usage_from_litellm_without_network() -> None:
    # litellm's mock_response exercises its real response parsing with no provider call.
    adapter: LLMPort = LiteLLMAdapter(
        models={ModelTier.LIGHT: "openai/gpt-4o-mini"},
        timeout_seconds=5,
        completion=partial(litellm.acompletion, mock_response="أهلاً"),
    )

    result = await adapter.complete(REQUEST)

    assert result.text == "أهلاً"
    assert result.input_tokens >= 0
    assert result.output_tokens >= 0


async def test_missing_tier_is_a_configuration_error() -> None:
    adapter = LiteLLMAdapter(models={}, timeout_seconds=5)

    with pytest.raises(LLMConfigurationError):
        await adapter.complete(REQUEST)


async def test_provider_timeout_is_retryable() -> None:
    async def timing_out(**_: Any) -> Any:
        raise litellm.exceptions.Timeout(message="slow", model="m", llm_provider="openai")

    adapter = LiteLLMAdapter(
        models={ModelTier.LIGHT: "openai/m"}, timeout_seconds=5, completion=timing_out
    )

    with pytest.raises(LLMUnavailableError):
        await adapter.complete(REQUEST)
