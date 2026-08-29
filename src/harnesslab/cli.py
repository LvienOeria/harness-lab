from __future__ import annotations

import json
import os
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .config import ModelConfig
from .env import load_dotenv
from .report import aggregate, render_markdown, save_records
from .runners import DshRunner, ReActRunner
from .tasks import list_tasks, load_task

console = Console()


@click.group()
def main() -> None:
    """harness-lab: reproducible agent harness evaluation for DeepSeek."""


@main.command("list-tasks")
def list_tasks_cmd() -> None:
    """List installed tasks."""
    table = Table(title="harness-lab tasks")
    table.add_column("id")
    table.add_column("suite")
    table.add_column("title")
    for task in list_tasks():
        table.add_row(task.id, task.suite, task.title)
    console.print(table)


def _model_config(model: str, temperature: float, max_tokens: int, thinking: bool, env_file: str) -> ModelConfig:
    load_dotenv(env_file)
    return ModelConfig(
        model=model,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL"),
        temperature=temperature,
        max_tokens=max_tokens,
        thinking=thinking,
    )


def _run_task(
    task_id: str,
    model_config: ModelConfig,
    runner_name: str,
    attempts: int,
    results_dir: str,
    graded_workspace_dir: str | None,
) -> None:
    task = load_task(task_id)
    runner = DshRunner(model_config) if runner_name == "dsh" else ReActRunner(model_config)
    out_dir = Path(results_dir) / runner_name / model_config.model.replace("/", "-") / task_id.replace("/", "-")
    out_dir.mkdir(parents=True, exist_ok=True)
    keep_dir = Path(graded_workspace_dir) if graded_workspace_dir else None
    records = []
    for attempt in range(1, attempts + 1):
        console.print(f"[bold]{task_id}[/bold] attempt {attempt}/{attempts} ...")
        record = runner.run_graded(
            task,
            attempt=attempt,
            trace_dir=out_dir / "traces",
            graded_workspace_dir=keep_dir,
        )
        records.append(record)
    agg = aggregate(records)
    save_records(records, out_dir / "records.json")
    (out_dir / "report.md").write_text(
        render_markdown(task_id, runner_name, model_config.model, records, agg), encoding="utf-8"
    )
    console.print_json(json.dumps(agg))


@main.command("run")
@click.option("--task", "task_id", required=True, help="Task id, e.g. file-ops/organize-by-extension")
@click.option("--model", default="deepseek-v4-flash", show_default=True)
@click.option("--runner", "runner_name", type=click.Choice(["react", "dsh"]), default="react", show_default=True)
@click.option("--attempts", default=3, show_default=True)
@click.option("--temperature", default=0.2, show_default=True)
@click.option("--max-tokens", default=8_192, show_default=True)
@click.option("--thinking/--no-thinking", default=False, show_default=True)
@click.option("--results-dir", default="results", show_default=True)
@click.option("--env-file", default=".env", show_default=True)
@click.option("--graded-workspace-dir", default=None, help="Optional directory to keep graded workspaces")
def run_cmd(
    task_id: str,
    model: str,
    runner_name: str,
    attempts: int,
    temperature: float,
    max_tokens: int,
    thinking: bool,
    results_dir: str,
    env_file: str,
    graded_workspace_dir: str | None,
) -> None:
    """Run one task, grade each attempt, and write records/report."""
    _run_task(
        task_id,
        _model_config(model, temperature, max_tokens, thinking, env_file),
        runner_name,
        attempts,
        results_dir,
        graded_workspace_dir,
    )


if __name__ == "__main__":
    main()
