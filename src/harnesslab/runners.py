from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

from .config import ModelConfig
from .graders import run_deterministic_grader
from .llm import DeepSeekClient, estimate_cost_usd
from .models import RunRecord, TaskSpec, ToolResult
from .tasks import load_task_handlers, make_workspace, task_dir
from .tools import WORKSPACE_TOOL_SCHEMAS, execute_workspace_tool

SYSTEM_PROMPT = """You are an autonomous agent solving a single, self-contained task inside a disposable workspace.
You have tools for inspecting and modifying files and for running safe shell commands.
Work step by step. Verify your final workspace state before you finish.
When you are done, stop calling tools and reply with a short summary of what you changed and why.
If a tool returns an error, read it carefully and retry with a corrected call.
Do not ask the user for clarification."""


def _tool_result_to_message(tool_result: ToolResult) -> dict[str, Any]:
    return {
        "role": "tool",
        "tool_call_id": tool_result.call_id,
        "content": tool_result.content,
    }


def _assistant_message_with_tool_calls(content: str, tool_calls: list[Any]) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": content or "",
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in tool_calls
        ],
    }


def _parse_arguments(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


class ReActRunner:
    """A deliberately minimal ReAct loop, used as the explainable baseline."""

    def __init__(self, model: ModelConfig):
        self.client = DeepSeekClient(model)
        self.model_config = model

    def _run_loop(self, task, workspace, record, trace_path, deadline):
        max_steps = int(task.limits.get("max_steps", 24))
        task_tools = []
        handlers = {}
        if task.tools == "task":
            task_tools = list(task.task_tools)
            handlers = load_task_handlers(task)
        else:
            task_tools = list(WORKSPACE_TOOL_SCHEMAS)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"# Task: {task.title}\n\n{task.prompt}\n\nWorkspace root: {workspace}"},
        ]

        def log_trace(obj):
            if trace_path is not None:
                with trace_path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(obj, ensure_ascii=False) + "\n")

        log_trace({"event": "start", "task_id": task.id, "workspace": str(workspace)})

        for _step in range(max_steps):
            if time.time() > deadline:
                record.error = "task timeout"
                break
            turn = self.client.chat(
                messages,
                tools=task_tools,
                max_tokens=int(task.limits.get("max_output_tokens", 8_192)),
            )
            record.input_tokens += turn.input_tokens
            record.output_tokens += turn.output_tokens
            record.steps += 1
            log_trace({
                "event": "llm_turn",
                "step": record.steps,
                "finish_reason": turn.finish_reason,
                "content": turn.content,
                "tool_calls": [{"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments} for tc in turn.tool_calls],
                "usage": {"input": turn.input_tokens, "output": turn.output_tokens},
            })

            if not turn.tool_calls:
                record.final_text = turn.content or ""
                record.finish_reason = turn.finish_reason
                return

            messages.append(_assistant_message_with_tool_calls(turn.content or "", turn.tool_calls))
            tool_results = []
            for tc in turn.tool_calls:
                name = tc.function.name
                args = _parse_arguments(tc.function.arguments)
                ok = True
                content = ""
                try:
                    if task.tools == "task":
                        handler = handlers.get(name)
                        if handler is None:
                            raise ValueError(f"no handler registered for task tool {name}")
                        content = str(handler(workspace, **args))
                    else:
                        content = execute_workspace_tool(workspace, name, args)
                except Exception as exc:
                    ok = False
                    content = f"error: {exc}"
                tool_results.append(ToolResult(name=name, call_id=tc.id, ok=ok, content=content))
                record.tool_calls += 1
                log_trace({"event": "tool_call", "name": name, "arguments": args, "ok": ok, "content": content[-4_000:]})
            messages.extend(_tool_result_to_message(result) for result in tool_results)
        record.error = f"max_steps exceeded ({max_steps})"

    def run(self, task, *, attempt=1, trace_dir=None, graded_workspace_dir=None):
        started = time.time()
        record = RunRecord(attempt=attempt, final_text="", passed=False, score=0.0)
        workspace, tmp_root = make_workspace(task)
        trace_path = None
        if trace_dir is not None:
            trace_path = trace_dir / f"{task.id.replace('/', '-')}-attempt-{attempt}.jsonl"
            trace_path.parent.mkdir(parents=True, exist_ok=True)
        timeout_seconds = int(task.limits.get("timeout_seconds", 600))
        deadline = time.time() + timeout_seconds
        try:
            self._run_loop(task, workspace, record, trace_path, deadline)
            if record.error is None:
                passed, details = run_deterministic_grader(task, task_dir(task.id), workspace)
                record.passed = passed
                record.score = float(details.get("score", 1.0 if passed else 0.0))
                record.grader_details = details
                if graded_workspace_dir is not None:
                    keep = graded_workspace_dir / task.id.replace("/", "-") / str(attempt)
                    keep.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(workspace, keep, dirs_exist_ok=True)
                    record.grader_details["graded_workspace"] = str(keep)
            record.cost_usd = estimate_cost_usd(self.model_config.model, record.input_tokens, record.output_tokens)
        except Exception as exc:
            record.error = f"{type(exc).__name__}: {exc}"
        finally:
            record.wall_seconds = time.time() - started
            record.trace_path = str(trace_path) if trace_path else None
            shutil.rmtree(tmp_root, ignore_errors=True)
        return record

    run_graded = run


class DshRunner:
    """Adapter for DeepSeek Harness (developer preview)."""

    def __init__(self, model: ModelConfig):
        self.model = model

    def run(self, task, *, attempt=1, trace_dir=None, graded_workspace_dir=None):
        record = RunRecord(attempt=attempt, final_text="", passed=False, score=0.0)
        record.error = "dsh adapter not wired in v0.1; use react runner (see docs/PRD.md)"
        return record

    run_graded = run
