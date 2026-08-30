# Benchmark report (v0.1 matrix)

- Date: 2026-08-30
- Model: `deepseek-v4-flash`
- Attempts: 1 per cell
- Tasks: 12

| task | runner | completion | mean steps | cost |
|---|---|---|---|---|
| data-clean/dedupe-csv | react | 100% | 6.0 | $0.003464 |
| data-clean/dedupe-csv | dsh | 100% | 3.0 | $0.000393 |
| data-clean/merge-csv | react | 100% | 5.0 | $0.001963 |
| data-clean/merge-csv | dsh | 100% | 3.0 | $0.000343 |
| data-clean/summarize-json | react | 100% | 6.0 | $0.002479 |
| data-clean/summarize-json | dsh | 100% | 3.0 | $0.000299 |
| file-ops/organize-by-extension | react | 100% | 4.0 | $0.001888 |
| file-ops/organize-by-extension | dsh | 100% | 4.0 | $0.000368 |
| file-ops/rename-dated-reports | react | 100% | 5.0 | $0.002517 |
| file-ops/rename-dated-reports | dsh | 100% | 6.0 | $0.000686 |
| file-ops/write-project-summary | react | 100% | 7.0 | $0.002466 |
| file-ops/write-project-summary | dsh | 100% | 3.0 | $0.000250 |
| long-qa/incident-log | react | 100% | 4.0 | $0.001435 |
| long-qa/incident-log | dsh | 100% | 3.0 | $0.000279 |
| long-qa/station-manual | react | 100% | 4.0 | $0.001504 |
| long-qa/station-manual | dsh | 100% | 3.0 | $0.000305 |
| mini-code/fix-mathutil | react | 100% | 6.0 | $0.003536 |
| mini-code/fix-mathutil | dsh | 100% | 13.0 | $0.001815 |
| mini-code/implement-fibonacci | react | 100% | 11.0 | $0.005028 |
| mini-code/implement-fibonacci | dsh | 100% | 10.0 | $0.001228 |
| tool-route/inventory-restock | react | 100% | 4.0 | $0.001109 |
| tool-route/inventory-restock | dsh | 100% | 4.0 | $0.000413 |
| tool-route/order-approval | react | 100% | 3.0 | $0.000980 |
| tool-route/order-approval | dsh | 100% | 14.0 | $0.005892 |

## Totals

| runner | tasks | completion | total cost |
|---|---|---|---|
| dsh | 12 | 100% | $0.012271 |
| react | 12 | 100% | $0.028369 |

## Repro

```bash
export DEEPSEEK_API_KEY=...
uv run harness-lab run-matrix --tasks all --runners react,dsh --models deepseek-v4-flash --attempts 1
```

## Notes

- dsh adapter uses the pinned DeepSeek Harness Python SDK (`sdk-minimal`, developer preview).
- dsh token accounting comes from session `assistant/message` usage events.
- All 12 tasks pass under both harnesses at attempt=1; differences are in step count and cost, not completion.
