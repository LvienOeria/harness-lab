# Benchmark report (v0.2, 25 tasks)

- Date: 2026-08-30
- Model: `deepseek-v4-flash`, temperature=0.2, attempts=1 per cell
- Tasks: 25 deterministic offline tasks across 5 suites
- Skills: task-defined skills enabled by default (`csv-data-ops`, `file-organization`)

## Runner completion

| runner | tasks | passed | notes |
|---|---|---|---|
| react | 25 | 25 | minimal ReAct baseline |
| dsh | 25 | 25 | DeepSeek Harness `sdk-minimal` adapter |
| react-compact | 5 measured | 4 | short tasks pass; `large-protocol` fails after compaction (see below) |

## react vs dsh cost summary

- `dsh` is consistently cheaper than `react` on short, tool-light tasks.
- `react` is more token-hungry because it carries the full JSON tool schema every turn and re-plans from scratch; `dsh` benefits from its persistent session and built-in tool/context management.
- Counter-example: `tool-route/order-approval` costs more under `dsh` (16 steps) than `react` (3 steps). Harness choice is task-dependent.

Representative rows (attempts=1):

| task | react steps | react cost | dsh steps | dsh cost |
|---|---|---|---|---|
| file-ops/organize-by-extension | 4 | $0.0015 | 4 | $0.00037 |
| data-clean/dedupe-csv | 6 | $0.0026 | 3 | $0.00039 |
| mini-code/fix-mathutil | 6 | $0.0035 | 10 | $0.0018 |
| tool-route/order-approval | 3 | $0.00098 | 16 | $0.0044 |
| long-qa/large-protocol | 9 | $0.0279 | 9 | $0.0197 |

## Skills ablation (react, 6 skill-tagged tasks)

Skills help data-clean tasks and slightly increase overhead on file-ops tasks:

| group | mean steps | mean cost |
|---|---|---|
| skills off | 5.2 | $0.00210 |
| skills on | 5.3 | $0.00246 |

Conclusion for now: skills are not a universal accelerator; their value depends on whether the task matches the procedural knowledge in the skill. This is consistent with the SkillsBench finding that focused skills help, while irrelevant context hurts.

## Compaction ablation

- `react-compact` passes 4/4 short tasks (compaction never triggers below 12k token budget).
- `long-qa/large-protocol` (180-section manual) passes with `react` in 9 steps at $0.0279, but `react-compact` fails with `max_steps exceeded` after 3 compactions at $0.0214.
- Interpretation: aggressive context compaction saved ~23% cost but lost task-relevant evidence in this task. Compaction needs a better retention policy before it is enabled by default.

## Repro

```bash
export DEEPSEEK_API_KEY=...
uv run harness-lab run-matrix --tasks all --runners react --attempts 1
uv run harness-lab run-matrix --tasks all --runners dsh --attempts 1
uv run harness-lab run --task long-qa/large-protocol --runner react-compact --attempts 1
```
