import shutil
from pathlib import Path

from harnesslab.graders import run_deterministic_grader
from harnesslab.tasks import list_tasks, load_task, make_workspace, task_dir


def test_all_tasks_have_fixtures_and_graders():
    tasks = list_tasks()
    assert len(tasks) >= 6
    for task in tasks:
        workspace, tmp = make_workspace(task)
        assert workspace.exists()
        shutil.rmtree(tmp, ignore_errors=True)


def test_grader_fails_on_untouched_workspace():
    task = load_task("file-ops/organize-by-extension")
    workspace, tmp = make_workspace(task)
    passed, _ = run_deterministic_grader(task, task_dir(task.id), workspace)
    assert passed is False
    shutil.rmtree(tmp, ignore_errors=True)


def test_grader_passes_on_correct_workspace():
    task = load_task("file-ops/organize-by-extension")
    workspace, tmp = make_workspace(task)
    (workspace / "text").mkdir()
    (workspace / "data").mkdir()
    for name in ["notes.txt", "report.md"]:
        (workspace / "incoming" / name).rename(workspace / "text" / name)
    for name in ["data.csv", "config.json"]:
        (workspace / "incoming" / name).rename(workspace / "data" / name)
    passed, _ = run_deterministic_grader(task, task_dir(task.id), workspace)
    assert passed is True
    shutil.rmtree(tmp, ignore_errors=True)
