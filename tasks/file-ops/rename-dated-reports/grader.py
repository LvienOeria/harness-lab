import json, os
from pathlib import Path
ws = Path(os.environ["WORKSPACE"]) / "reports"
dates = ["20240801","20231231","20250704","20261120"]
problems=[]
for d in dates:
    new = ws / f"{d[:4]}-{d[4:6]}-{d[6:]}-report.md"
    old = ws / f"report_{d}.md"
    if old.exists(): problems.append(f"old name still exists: {old.name}")
    if not new.exists(): problems.append(f"missing {new.name}")
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
