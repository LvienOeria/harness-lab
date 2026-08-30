import csv, json, os
from pathlib import Path
ws = Path(os.environ["WORKSPACE"])
p = ws / "category_totals.csv"
problems = []
if not p.exists():
    problems.append("missing category_totals.csv")
else:
    rows = list(csv.DictReader(p.read_text().splitlines()))
    try:
        normalized = [{"category": r["category"], "total": round(float(r["total"]), 2)} for r in rows]
    except (KeyError, ValueError) as exc:
        normalized = []
        problems.append(f"bad csv: {exc}")
    expected = [{"category": "books", "total": 16.0}, {"category": "figures", "total": 7.0}, {"category": "games", "total": 20.0}]
    if normalized != expected:
        problems.append(f"expected {expected}, got {normalized}")
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
