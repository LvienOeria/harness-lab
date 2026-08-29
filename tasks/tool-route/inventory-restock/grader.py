import json
import os
from pathlib import Path

ws = Path(os.environ["WORKSPACE"])
data = json.loads((ws / "inventory.json").read_text())
expected = {"medkit": 20, "battery": 20, "ration": 8, "fuel_cell": 20, "cable": 12}
problems = []
for key, value in expected.items():
    if key not in data:
        problems.append(f"missing {key}")
    elif data[key] != value:
        problems.append(f"{key}: expected {value}, got {data[key]}")
if any(k not in expected for k in data):
    problems.append(f"unexpected keys: {[k for k in data if k not in expected]}")
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
