import json, os
from pathlib import Path
ws = Path(os.environ["WORKSPACE"]) / "logs"
problems = []
expected_archive = ["2022-06-15.log", "2023-12-31.log"]
expected_root = ["2024-01-01.log", "2024-06-15.log"]
if sorted(p.name for p in (ws / "archive").glob("*.log")) != expected_archive:
    problems.append("archive contents wrong")
if sorted(p.name for p in ws.glob("*.log")) != expected_root:
    problems.append("root logs wrong")
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
