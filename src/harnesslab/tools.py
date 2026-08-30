from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

WORKSPACE_TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories inside the workspace. Pass a relative path or '.' for the workspace root.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Relative directory path."}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a UTF-8 text file inside the workspace. Use it before editing data or answering questions.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Relative file path."}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a UTF-8 text file inside the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path."},
                    "content": {"type": "string", "description": "Complete file content."},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": (
                "Run a single shell command in the workspace. Prefer standard utilities: "
                "ls, cat, cp, mv, mkdir, rm, find, grep, sort, uniq, head, tail, wc, python, pytest. "
                "Network commands and interactive commands are forbidden."
            ),
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "Shell command to run."}},
                "required": ["command"],
            },
        },
    },
]

_FORBIDDEN_PATTERNS = (
    "curl", "wget", "nc ", "ncat", "ssh", "scp", "sudo", "osascript",
    "http.server", "shutdown", "reboot",
)

_ALLOWED_COMMANDS = {
    "ls", "cat", "cp", "mv", "mkdir", "rm", "find", "grep", "sort", "uniq",
    "head", "tail", "wc", "python", "pytest", "sed", "awk", "printf", "echo",
    "touch", "chmod", "diff", "cut", "tr", "xargs", "basename", "dirname",
    "readlink", "pwd", "date", "expr", "true", "false", "test", "cd",
}


def _resolve_workspace_path(root: Path, rel: str) -> Path:
    rel = rel.strip()
    candidate = (root / rel).resolve()
    root_resolved = root.resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ValueError(f"path escapes workspace: {rel!r}")
    return candidate


def _format_listing(root: Path, rel: str = ".") -> str:
    target = _resolve_workspace_path(root, rel)
    if not target.exists():
        return f"error: path does not exist: {rel}"
    if not target.is_dir():
        return f"error: not a directory: {rel}"
    lines = []
    for p in sorted(target.rglob("*")):
        kind = "dir" if p.is_dir() else "file"
        lines.append(f"{kind}\t{p.relative_to(root)}")
    if not lines:
        return "(empty directory)"
    return "\n".join(lines)


def _read_file(root: Path, rel: str, max_bytes: int = 50_000) -> str:
    target = _resolve_workspace_path(root, rel)
    if not target.is_file():
        return f"error: file does not exist or is not a file: {rel}"
    data = target.read_bytes()
    if len(data) > max_bytes:
        return f"error: file too large ({len(data)} bytes); max read is {max_bytes}."
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return f"error: binary file ({len(data)} bytes): {rel}"


def _write_file(root: Path, rel: str, content: str) -> str:
    target = _resolve_workspace_path(root, rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"wrote {len(content.encode('utf-8'))} bytes to {rel}"


def _run_shell(root: Path, command: str, timeout: int = 120) -> str:
    command = command.strip()
    if not command:
        return "error: empty command"
    lowered = command.lower()
    for pattern in _FORBIDDEN_PATTERNS:
        if pattern in lowered:
            return f"error: forbidden command pattern detected: {pattern}"
    argv = shlex.split(command)
    if not argv:
        return "error: cannot parse command"
    executable = os.path.basename(argv[0])
    if executable not in _ALLOWED_COMMANDS:
        allowed = ", ".join(sorted(_ALLOWED_COMMANDS))
        return f"error: command not allowed: {executable}. Allowed: {allowed}"
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=root,
            env={
                **os.environ,
                "PYTHONPATH": str(root),
                "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", ""),
            },
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"error: command timed out after {timeout}s"
    out = (proc.stdout or "")[-8_000:]
    err = (proc.stderr or "")[-4_000:]
    result = f"exit={proc.returncode}\nstdout:\n{out}"
    if err:
        result += f"\nstderr:\n{err}"
    return result


def execute_workspace_tool(root: Path, name: str, arguments: dict[str, Any]) -> str:
    if name == "list_files":
        return _format_listing(root, str(arguments.get("path", ".")))
    if name == "read_file":
        return _read_file(root, str(arguments.get("path", "")))
    if name == "write_file":
        return _write_file(root, str(arguments.get("path", "")), str(arguments.get("content", "")))
    if name == "run_shell":
        return _run_shell(root, str(arguments.get("command", "")))
    return f"error: unknown workspace tool: {name}"
