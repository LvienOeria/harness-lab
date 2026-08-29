from __future__ import annotations

import json
from pathlib import Path

from .models import RunRecord

METRIC_ORDER = [
    "completion",
    "score",
    "steps",
    "tool_calls",
    "input_tokens",
    "output_tokens",
    "cost_usd",
    "wall_seconds",
]


def aggregate(records: list[RunRecord]) -> dict:
    if not records:
        return {}
    attempts = len(records)
    passed = [r for r in records if r.passed]
    completion = len(passed) / attempts
    scores = [r.score for r in records]
    return {
        "attempts": attempts,
        "passes": len(passed),
        "completion": round(completion, 4),
        "pass_at_1": round(completion, 4),
        "mean_score": round(sum(scores) / attempts, 4) if scores else 0.0,
        "mean_steps": round(sum(r.steps for r in records) / attempts, 2),
        "mean_tool_calls": round(sum(r.tool_calls for r in records) / attempts, 2),
        "mean_input_tokens": round(sum(r.input_tokens for r in records) / attempts, 1),
        "mean_output_tokens": round(sum(r.output_tokens for r in records) / attempts, 1),
        "total_cost_usd": round(sum(r.cost_usd for r in records), 6),
        "mean_wall_seconds": round(sum(r.wall_seconds for r in records) / attempts, 2),
        "errors": [r.error for r in records if r.error],
    }


def save_records(records: list[RunRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump([_record_to_dict(r) for r in records], fh, ensure_ascii=False, indent=2)


def _record_to_dict(record: RunRecord) -> dict:
    return {
        "attempt": record.attempt,
        "final_text": record.final_text[:4_000],
        "passed": record.passed,
        "score": record.score,
        "grader_details": record.grader_details,
        "steps": record.steps,
        "input_tokens": record.input_tokens,
        "output_tokens": record.output_tokens,
        "cost_usd": record.cost_usd,
        "wall_seconds": record.wall_seconds,
        "tool_calls": record.tool_calls,
        "finish_reason": record.finish_reason,
        "error": record.error,
        "trace_path": record.trace_path,
    }


def render_markdown(task_id: str, runner: str, model: str, records: list[RunRecord], aggregate_: dict) -> str:
    lines = [
        f"# Benchmark run: {task_id}",
        "",
        f"- runner: `{runner}`",
        f"- model: `{model}`",
        f"- attempts: {aggregate_.get('attempts', 0)}",
        f"- completion: **{aggregate_.get('completion', 0):.2%}**",
        f"- mean steps: {aggregate_.get('mean_steps', 0)}",
        f"- mean tool calls: {aggregate_.get('mean_tool_calls', 0)}",
        f"- total cost (USD): {aggregate_.get('total_cost_usd', 0):.6f}",
        "",
    ]
    for record in records:
        lines.append(
            f"- attempt {record.attempt}: passed={record.passed}, steps={record.steps}, "
            f"tokens={record.input_tokens}/{record.output_tokens}, error={record.error or '-'}"
        )
    lines.append("")
    return "\n".join(lines)
