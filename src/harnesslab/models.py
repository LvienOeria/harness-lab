from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field


class GraderSpec(BaseModel):
    type: Literal["python"] = "python"
    script: str = "grader.py"


class TaskSpec(BaseModel):
    id: str
    suite: str
    title: str
    prompt: str
    workspace: str = "workspace"
    grader: GraderSpec = Field(default_factory=GraderSpec)
    limits: dict[str, Any] = Field(default_factory=dict)
    tools: Literal["workspace", "task"] = "workspace"
    task_tools: list[dict[str, Any]] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    task_handlers: str | None = None
    notes: str = ""


@dataclass
class ToolResult:
    name: str
    call_id: str
    ok: bool
    content: str


@dataclass
class RunRecord:
    attempt: int
    final_text: str
    passed: bool
    score: float
    grader_details: dict[str, Any] = field(default_factory=dict)
    steps: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    wall_seconds: float = 0.0
    tool_calls: int = 0
    compactions: int = 0
    finish_reason: str | None = None
    error: str | None = None
    trace_path: str | None = None
