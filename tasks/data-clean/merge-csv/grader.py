import csv, json, os
from pathlib import Path
ws = Path(os.environ["WORKSPACE"])
p = ws / "merged.csv"
problems = []
if not p.exists():
    problems.append("missing merged.csv")
else:
    rows = list(csv.DictReader(p.read_text().splitlines()))
    expected = [{"id":"1","name":"Ana","city":"Lagos"},{"id":"3","name":"Cid","city":"Osaka"},{"id":"4","name":"Dee","city":"Lima"}]
    if rows != expected:
        problems.append(f"expected {expected}, got {rows}")
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
