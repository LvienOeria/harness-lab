import json, os
from pathlib import Path
ws = Path(os.environ["WORKSPACE"])
p = ws / "active_users.json"
problems = []
if not p.exists():
    problems.append("missing active_users.json")
else:
    data = json.loads(p.read_text())
    expected = [{"id": 2, "name": "B", "active": True}, {"id": 3, "name": "C", "active": True}]
    if data != expected:
        problems.append(f"expected {expected}, got {data}")
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
