from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .models import TaskSpec

TASKS_ROOT = Path(__file__).resolve().parents[2] / "tasks"


def task_dir(task_id: str) -> Path:
    path = TASKS_ROOT / task_id
    if not path.exists():
        raise FileNotFoundError(f"unknown task: {task_id} (looked in {path})")
    return path


def load_task(task_id: str) -> TaskSpec:
    raw = json.loads((task_dir(task_id) / "task.json").read_text(encoding="utf-8"))
    return TaskSpec.model_validate(raw)


def list_tasks() -> list[TaskSpec]:
    out = []
    for path in sorted(TASKS_ROOT.rglob("task.json")):
        spec = TaskSpec.model_validate(json.loads(path.read_text(encoding="utf-8")))
        out.append(spec)
    return out


def make_workspace(task: TaskSpec) -> tuple[Path, Path]:
    src = task_dir(task.id) / task.workspace
    if not src.exists():
        raise FileNotFoundError(f"task workspace missing: {src}")
    tmp = tempfile.mkdtemp(prefix=f"harness-lab-{task.id.replace('/', '-')}-")
    target = Path(tmp) / "workspace"
    shutil.copytree(src, target)
    return target, tmp


def load_task_handlers(task: TaskSpec) -> dict[str, Any]:
    if not task.task_handlers:
        return {}
    path = task_dir(task.id) / task.task_handlers
    namespace: dict[str, Any] = {}
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace)
    return namespace.get("HANDLERS", {})
