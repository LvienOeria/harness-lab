import json, os
from pathlib import Path
ws = Path(os.environ["WORKSPACE"])
p = ws / "project_summary.md"
problems = []
if not p.exists():
    problems.append("missing project_summary.md")
else:
    text = p.read_text()
    checks = ["## Name\nProject Orion", "## Owner\nLin Chen", "## Status\nActive"]
    for c in checks:
        if c not in text:
            problems.append("missing " + c.replace("\n", " / "))
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
