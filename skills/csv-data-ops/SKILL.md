---
name: csv-data-ops
description: Use when a task asks to clean, merge, deduplicate, or summarize CSV data.
---

# CSV data operations

- Prefer `python` with the standard-library `csv` module over shell text tools.
- Use `csv.DictReader` and `csv.DictWriter`; preserve header names and column order.
- For deduplication, choose the business key from the task (usually `id`) and keep one row per key.
- Sort output by the key requested in the task, in ascending order.
- Write results to the exact filename requested by the task.
- Verify the output by reading the first few rows before finishing.
