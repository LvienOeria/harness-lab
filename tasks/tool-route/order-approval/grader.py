import json, os
from pathlib import Path
ws = Path(os.environ["WORKSPACE"])
state = json.loads((ws / "state.json").read_text())
problems = []
expected = ["o-1"]
if state.get("approved") != expected:
    problems.append(f"approved={state.get('approved')} expected {expected}")
if state.get("rejected") != ["o-2"]:
    problems.append(f"rejected={state.get('rejected')} expected ['o-2']")
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
