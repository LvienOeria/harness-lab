from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    provider: str = "deepseek"
    model: str = "deepseek-v4-flash"
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.2
    max_tokens: int = 8_192
    thinking: bool = False
    reasoning_effort: str | None = None


@dataclass
class RunLimits:
    max_steps: int = 24
    max_output_tokens: int = 8_192
    timeout_seconds: int = 600


@dataclass
class EvalConfig:
    attempts: int = 3
    seed: int = 42
    results_dir: str = "results"
