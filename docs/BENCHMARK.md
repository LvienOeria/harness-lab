# Benchmark report (v0.1 smoke)

- Date: 2026-08-30
- Runner: `react` (minimal ReAct baseline)
- Model: `deepseek-v4-flash`, non-thinking, temperature=0.2
- Attempts: 1 per task
- Task count: 7
- Completion: **7 / 7**
- Total model cost: **$0.0183**

| task | passed | steps | tool_calls | input tokens | output tokens | cost_usd | seconds |
|---|---|---|---|---|---|---|---|
| data-clean/dedupe-csv | ✅ | 4 | 4 | 4814 | 549 | 0.001421 | 5.02 |
| data-clean/summarize-json | ✅ | 9 | 10 | 16312 | 1461 | 0.004553 | 14.92 |
| file-ops/organize-by-extension | ✅ | 4 | 4 | 4763 | 590 | 0.001437 | 5.76 |
| file-ops/rename-dated-reports | ✅ | 6 | 6 | 10179 | 1100 | 0.002965 | 9.69 |
| long-qa/station-manual | ✅ | 4 | 3 | 4998 | 451 | 0.001397 | 4.82 |
| mini-code/fix-mathutil | ✅ | 8 | 9 | 18687 | 2033 | 0.005453 | 17.77 |
| tool-route/inventory-restock | ✅ | 4 | 5 | 3638 | 479 | 0.001117 | 5.32 |

## Repro

```bash
export DEEPSEEK_API_KEY=...
uv run harness-lab run --task <task-id> --runner react --attempts 1
```

## Notes

- This is a smoke baseline for the ReAct runner, not yet a capability/regression split.
- `tool-route` exposes only structured task tools; file and shell tools are disabled.
- Deterministic graders check the final workspace or written artifacts.
