import json, os
from pathlib import Path
ws = Path(os.environ["WORKSPACE"])
state = json.loads((ws / "state.json").read_text())
problems = []
if not state.get("quotes"):
    problems.append("no quote recorded")
else:
    q = state["quotes"][-1]
    if q.get("unit_price") != 340.0 or q.get("quantity") != 4:
        problems.append(f"bad quote {q}")
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
