from pathlib import Path

from harnesslab.tools import execute_workspace_tool


def test_list_and_write_read(tmp_path: Path):
    (tmp_path / "a.txt").write_text("hello")
    out = execute_workspace_tool(tmp_path, "list_files", {"path": "."})
    assert "a.txt" in out
    assert "wrote" in execute_workspace_tool(tmp_path, "write_file", {"path": "b.txt", "content": "world"})
    assert execute_workspace_tool(tmp_path, "read_file", {"path": "b.txt"}) == "world"


def test_path_escape_blocked(tmp_path: Path):
    try:
        execute_workspace_tool(tmp_path, "read_file", {"path": "../secret"})
    except ValueError as exc:
        assert "escapes workspace" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_forbidden_shell_command(tmp_path: Path):
    out = execute_workspace_tool(tmp_path, "run_shell", {"command": "curl example.com"})
    assert "forbidden" in out


def test_allowed_shell_command(tmp_path: Path):
    out = execute_workspace_tool(tmp_path, "run_shell", {"command": "echo hi"})
    assert "hi" in out
