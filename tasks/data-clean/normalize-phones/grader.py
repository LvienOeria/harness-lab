import csv, json, os
from pathlib import Path
ws = Path(os.environ["WORKSPACE"])
p = ws / "contacts_normalized.csv"
problems = []
if not p.exists():
    problems.append("missing contacts_normalized.csv")
else:
    rows = list(csv.DictReader(p.read_text().splitlines()))
    expected = [{"id": "1", "name": "Ana", "phone": "+1-5550101234"}, {"id": "2", "name": "Bo", "phone": "+1-5550105678"}, {"id": "3", "name": "Cid", "phone": "+1-5550109999"}]
    if rows != expected:
        problems.append(f"expected {expected}, got {rows}")
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
