import csv, json, os
from pathlib import Path
ws=Path(os.environ["WORKSPACE"])
problems=[]
p=ws/"sales_clean.csv"
if not p.exists(): problems.append("missing sales_clean.csv")
else:
    rows=list(csv.DictReader(p.read_text().splitlines()))
    seen=[]
    for r in rows: seen.append(tuple(r.values()))
    if rows != sorted(rows, key=lambda r: int(r['id'])): problems.append("not sorted by id")
    if len(rows)!=3: problems.append(f"expected 3 unique rows, got {len(rows)}")
    expected={'1','2','3'}
    if {r['id'] for r in rows} != expected: problems.append("wrong ids")
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
