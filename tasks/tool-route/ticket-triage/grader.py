import json, os
from pathlib import Path
ws = Path(os.environ["WORKSPACE"])
state = json.loads((ws / "tickets.json").read_text())
expected = {"t-1": "urgent", "t-2": "normal", "t-3": "urgent"}
problems = []
if state.get("statuses") != expected:
    problems.append(f"expected {expected}, got {state.get('statuses')}")
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
