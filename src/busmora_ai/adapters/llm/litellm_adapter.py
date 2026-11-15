"""LLMPort over the LiteLLM SDK (not the proxy). The only module that imports litellm."""

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

import litellm
from litellm import exceptions as litellm_errors

from busmora_ai.application.ports.llm import (
    CompletionRequest,
    CompletionResult,
    LLMConfigurationError,
    LLMUnavailableError,
    ModelTier,
)

CompletionFn = Callable[..., Awaitable[Any]]

_RETRYABLE: tuple[type[Exception], ...] = (
    litellm_errors.Timeout,
    litellm_errors.APIConnectionError,
    litellm_errors.RateLimitError,
    litellm_errors.ServiceUnavailableError,
    litellm_errors.InternalServerError,
)
_CONFIGURATION: tuple[type[Exception], ...] = (
    litellm_errors.AuthenticationError,
    litellm_errors.NotFoundError,
)


class LiteLLMAdapter:
    def __init__(
        self,
        *,
        models: Mapping[ModelTier, str],
        timeout_seconds: float,
        completion: CompletionFn = litellm.acompletion,
    ) -> None:
        self._models = dict(models)
        self._timeout_seconds = timeout_seconds
        self._completion = completion

    async def complete(self, request: CompletionRequest) -> CompletionResult:
        model = self._models.get(request.tier)
        if model is None:
            msg = f"No model configured for tier {request.tier.value!r}"
            raise LLMConfigurationError(msg)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "timeout": self._timeout_seconds,
        }
        if request.max_output_tokens is not None:
            kwargs["max_tokens"] = request.max_output_tokens
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature

        try:
            response = await self._completion(**kwargs)
        except _CONFIGURATION as exc:
            raise LLMConfigurationError(type(exc).__name__) from exc
        except _RETRYABLE as exc:
            raise LLMUnavailableError(type(exc).__name__) from exc

        return _to_result(response, requested_model=model)


def _to_result(response: Any, *, requested_model: str) -> CompletionResult:
    choice = response.choices[0]
    usage = getattr(response, "usage", None)
    return CompletionResult(
        text=str(choice.message.content or ""),
        model=str(getattr(response, "model", None) or requested_model),
        input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
        output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
        cost_micro_usd=_cost_micro_usd(response),
    )


def _cost_micro_usd(response: Any) -> int | None:
    try:
        cost = float(litellm.completion_cost(completion_response=response))
    except Exception:  # noqa: BLE001 - unknown prices must not fail the call
        return None
    return round(cost * 1_000_000)
