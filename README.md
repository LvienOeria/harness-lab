# harness-lab

> 中文：一个面向 DeepSeek Harness 的可复现评测台，量化 agent loop、compaction、skill 与工具集配置对完成率和成本的影响。
> English: An evaluation harness for DeepSeek Harness that benchmarks agent loops, compaction, skills, and tool configurations on reproducible offline tasks.

## Why

The same model can produce very different results under different harness configurations. `harness-lab` runs deterministic offline tasks through a minimal ReAct baseline and (in progress) DeepSeek Harness, then reports completion, tokens, cost, steps, and failure classes.

## Demo

_Coming in M4._

## Quickstart

```bash
uv venv .venv
uv pip install -e .
export DEEPSEEK_API_KEY=sk-...
uv run harness-lab list-tasks
uv run harness-lab run --task file-ops/organize-by-extension --runner react --attempts 3
```

Without an API key, all task fixtures and graders still run offline:

```bash
uv run pytest
```

## Architecture

```text
src/harnesslab/
  llm.py       DeepSeek V4 client + token cost model
  tools.py     sandboxed workspace tools (list/read/write/shell)
  runners.py   ReAct baseline; DeepSeek Harness adapter (preview)
  tasks.py     task loader and disposable workspace factory
  graders.py   deterministic grader runner
  report.py    aggregation and markdown reports
tasks/         6 deterministic offline tasks (file-ops, data-clean, mini-code, long-qa)
```

## Evaluation

- Every task has an immutable fixture workspace, a deterministic grader, and per-task budgets.
- Each configuration runs N attempts and reports completion, pass@1, token usage, USD cost, steps, tool calls, and errors.
- Capability and regression suites will be separated in the full benchmark (see `docs/PRD.md`).

## PM Artifacts

- `docs/PRD.md`
- `docs/ADR/`
- `docs/BENCHMARK.md` (generated)

## Roadmap

- M1: task framework + ReAct baseline + first task suite.
- M2: DeepSeek Harness adapter (pinned preview version).
- M3: 24 tasks, configuration matrix, failure classifier.
- M4: Streamlit dashboard, benchmark report, demo.

## License

MIT
