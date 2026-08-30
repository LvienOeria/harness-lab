import json, os
from pathlib import Path
ws = Path(os.environ["WORKSPACE"])
p = ws / "decision.md"
problems = []
if not p.exists():
    problems.append("missing decision.md")
else:
    text = p.read_text().lower()
    if "denied" not in text and "reject" not in text and "not approved" not in text:
        problems.append("wrong decision")
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
