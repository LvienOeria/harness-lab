from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from .config import ModelConfig


@dataclass
class LLMTurn:
    content: str | None
    tool_calls: list[Any]
    input_tokens: int
    output_tokens: int
    finish_reason: str | None
    raw: Any


class DeepSeekClient:
    """Thin OpenAI-compatible client for DeepSeek V4."""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key or "not-set",
            base_url=config.base_url or "https://api.deepseek.com",
            timeout=300,
            max_retries=3,
        )

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        *,
        max_tokens: int | None = None,
    ) -> LLMTurn:
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        if self.config.thinking:
            kwargs["extra_body"] = {
                "thinking": {"type": "enabled"},
                **({"reasoning_effort": self.config.reasoning_effort} if self.config.reasoning_effort else {}),
            }
        started = time.time()
        response = self.client.chat.completions.create(**kwargs)
        elapsed = time.time() - started
        choice = response.choices[0]
        message = choice.message
        usage = getattr(response, "usage", None)
        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        if input_tokens == 0:
            input_tokens = int(getattr(usage, "prompt_cache_hit_tokens", 0) or 0) + int(
                getattr(usage, "prompt_cache_miss_tokens", 0) or 0
            )
        return LLMTurn(
            content=message.content,
            tool_calls=list(message.tool_calls or []),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            finish_reason=choice.finish_reason,
            raw=response,
        )


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Off-peak list prices for DeepSeek V4, USD per 1M tokens."""
    if model.startswith("deepseek-v4-pro"):
        in_price, out_price = 0.66, 1.98
    else:
        in_price, out_price = 0.22, 0.66
    return input_tokens / 1_000_000 * in_price + output_tokens / 1_000_000 * out_price
