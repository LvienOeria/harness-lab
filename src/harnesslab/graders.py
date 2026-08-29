from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from .models import TaskSpec


class GraderFailure(RuntimeError):
    pass


def _last_json_stdout(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line or line.startswith("{") is False:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def run_deterministic_grader(task: TaskSpec, task_root: Path, workspace: Path) -> tuple[bool, dict[str, Any]]:
    grader_path = task_root / task.grader.script
    if not grader_path.exists():
        raise GraderFailure(f"grader missing: {grader_path}")
    proc = subprocess.run(
        [sys.executable, str(grader_path)],
        cwd=task_root,
        env={**os.environ, "WORKSPACE": str(workspace), "TASK_ROOT": str(task_root)},
        capture_output=True,
        text=True,
        timeout=180,
    )
    details: dict[str, Any] = {
        "exit_code": proc.returncode,
        "stdout_tail": (proc.stdout or "")[-4_000:],
        "stderr_tail": (proc.stderr or "")[-2_000:],
    }
    payload = _last_json_stdout(proc.stdout or "")
    passed = proc.returncode == 0 and bool(payload and payload.get("passed") is True)
    if payload:
        details["grader"] = payload
        if "score" in payload:
            details["score"] = float(payload["score"])
    if not passed and payload:
        details["reason"] = payload.get("reason", payload.get("message", "check failed"))
    return passed, details
