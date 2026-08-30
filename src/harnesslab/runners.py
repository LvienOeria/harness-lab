from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any

from .config import ModelConfig
from .graders import run_deterministic_grader
from .llm import DeepSeekClient, estimate_cost_usd
from .models import RunRecord, TaskSpec, ToolResult
from .skills import inject_skills
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

    def __init__(self, model: ModelConfig, extra_skills: list[str] | None = None):
        self.client = DeepSeekClient(model)
        self.model_config = model
        self.extra_skills = None if extra_skills is None else list(extra_skills)

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

    def _compact_if_needed(self, messages, record, token_budget, trace_path):
        if token_budget <= 0 or len(messages) <= 3:
            return
        current_estimate = sum((len(json.dumps(m, ensure_ascii=False)) // 4) for m in messages)
        if current_estimate < token_budget:
            return
        history = messages[1:]
        prompt = (
            "Summarize the agent conversation below into compact working memory. "
            "Preserve the original task, files inspected or changed, current workspace state, "
            "constraints, and next actions."
        )
        summary_turn = self.client.chat(
            [
                {"role": "system", "content": "You are a context-compaction assistant."},
                {
                    "role": "user",
                    "content": f"{prompt}\n\n<conversation>\n{json.dumps(history, ensure_ascii=False)[-40_000:]}\n</conversation>",
                },
            ],
            max_tokens=1_000,
        )
        record.input_tokens += summary_turn.input_tokens
        record.output_tokens += summary_turn.output_tokens
        record.compactions += 1
        summary = summary_turn.content or ""
        latest = messages[-1].get("content", "") if messages[-1].get("role") == "tool" else ""
        compacted = f"[compacted working memory]\n\n{summary}"
        if latest:
            compacted += f"\n\nLatest tool result:\n{latest[-6_000:]}"
        compacted += "\n\nContinue the task."
        messages[:] = [
            messages[0],
            {"role": "user", "content": compacted},
        ]
        if trace_path is not None:
            with trace_path.open("a", encoding="utf-8") as fh:
                fh.write(
                    json.dumps(
                        {"event": "compaction", "tokens_before": record.input_tokens, "summary": summary[:2_000]},
                        ensure_ascii=False,
                    )
                    + "\n"
                )

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


class CompactReActRunner(ReActRunner):
    """ReAct baseline with context compaction enabled after a token budget."""

    def __init__(self, model: ModelConfig, extra_skills: list[str] | None = None, compact_after_tokens: int = 12_000):
        super().__init__(model, extra_skills=extra_skills)
        self.extra_skills = None if extra_skills is None else list(extra_skills)
        self.compact_after_tokens = compact_after_tokens

    def _run_loop(self, task, workspace, record, trace_path, deadline):
        max_steps = int(task.limits.get("max_steps", 24))
        task_tools = []
        handlers = {}
        if task.tools == "task":
            task_tools = list(task.task_tools)
            handlers = load_task_handlers(task)
        else:
            task_tools = list(WORKSPACE_TOOL_SCHEMAS)

        skill_names = self.extra_skills if self.extra_skills is not None else list(task.skills)
        messages = [
            {"role": "system", "content": inject_skills(SYSTEM_PROMPT, skill_names)},
            {"role": "user", "content": f"# Task: {task.title}\n\n{task.prompt}\n\nWorkspace root: {workspace}"},
        ]

        def log_trace(obj):
            if trace_path is not None:
                with trace_path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(obj, ensure_ascii=False) + "\n")

        for _step in range(max_steps):
            if time.time() > deadline:
                record.error = "task timeout"
                break
            self._compact_if_needed(messages, record, self.compact_after_tokens, trace_path)
            turn = self.client.chat(messages, tools=task_tools, max_tokens=int(task.limits.get("max_output_tokens", 8_192)))
            record.input_tokens += turn.input_tokens
            record.output_tokens += turn.output_tokens
            record.steps += 1
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


class DshRunner:
    """Adapter for DeepSeek Harness (developer preview, pinned dsh-v0.1.2-alpha.1)."""

    def __init__(self, model: ModelConfig):
        self.model = model
        self._home = Path("sessions/dsh-home").resolve()
        self._workspace_root = Path("sessions/dsh-workspace").resolve()
        self._home.mkdir(parents=True, exist_ok=True)
        self._workspace_root.mkdir(parents=True, exist_ok=True)

    def _fresh_workspace_for(self, task: TaskSpec, attempt: int) -> Path:
        workspace = self._workspace_root / task.id.replace("/", "-") / str(attempt)
        if workspace.exists():
            shutil.rmtree(workspace, ignore_errors=True)
        workspace.mkdir(parents=True)
        fixture, tmp = make_workspace(task)
        for item in fixture.iterdir():
            target = workspace / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
        shutil.rmtree(tmp, ignore_errors=True)
        return workspace

    def _run_once(self, task: TaskSpec, workspace: Path, attempt: int):
        from deepseek_harness import DeepSeekHarness  # type: ignore

        session_id = f"{task.id.replace('/', '-')}-attempt-{attempt}"
        with DeepSeekHarness(
            provider="deepseek-official",
            model=self.model.model,
            max_tokens=self.model.max_tokens,
            cwd=str(workspace),
            dsh_home=str(self._home),
            profile="sdk-minimal",
        ) as harness:
            return harness.run(task.prompt, session_id=session_id)

    def _apply_usage(self, record: RunRecord, events: list[Any]) -> None:
        for event in events:
            if not isinstance(event, dict):
                continue
            etype = event.get("type")
            data = event.get("data", {}) if isinstance(event.get("data"), dict) else {}
            if etype == "step/start":
                record.steps += 1
            elif etype == "tool/call":
                record.tool_calls += 1
            elif etype == "assistant/message":
                usage = data.get("usage") or data.get("message", {}).get("usage") or {}
                record.input_tokens += int(usage.get("inputTokens", 0) or 0)
                record.output_tokens += int(usage.get("outputTokens", 0) or 0)

    def run(
        self,
        task: TaskSpec,
        *,
        attempt: int = 1,
        trace_dir: Path | None = None,
        graded_workspace_dir: Path | None = None,
    ) -> RunRecord:
        started = time.time()
        record = RunRecord(attempt=attempt, final_text="", passed=False, score=0.0)
        workspace = self._fresh_workspace_for(task, attempt)
        try:
            result = None
            try:
                result = self._run_once(task, workspace, attempt)
            except FileNotFoundError as exc:
                if "runtime" not in str(exc).lower():
                    raise
                os.environ["DSH_RUNTIME_MODE"] = "node"
                result = self._run_once(task, workspace, attempt)
            record.final_text = result.final_response or ""
            record.finish_reason = str(getattr(result, "finish_reason", None))
            self._apply_usage(record, list(getattr(result, "events", []) or []))
            record.cost_usd = estimate_cost_usd(self.model.model, record.input_tokens, record.output_tokens)
            passed, details = run_deterministic_grader(task, task_dir(task.id), workspace)
            record.passed = passed
            record.score = float(details.get("score", 1.0 if passed else 0.0))
            record.grader_details = details
            if graded_workspace_dir is not None:
                keep = graded_workspace_dir / task.id.replace("/", "-") / str(attempt)
                keep.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(workspace, keep, dirs_exist_ok=True)
                record.grader_details["graded_workspace"] = str(keep)
        except Exception as exc:  # noqa: BLE001
            record.error = f"{type(exc).__name__}: {exc}"
        finally:
            record.wall_seconds = time.time() - started
            if trace_dir:
                trace_dir.mkdir(parents=True, exist_ok=True)
                record.trace_path = str(trace_dir / f"{task.id.replace('/', '-')}-dsh-{attempt}.txt")
                Path(record.trace_path).write_text(
                    json.dumps(
                        {
                            "final_text": record.final_text,
                            "error": record.error,
                            "input_tokens": record.input_tokens,
                            "output_tokens": record.output_tokens,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
        return record

    run_graded = run
