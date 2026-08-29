import json, os
from pathlib import Path
ws=Path(os.environ["WORKSPACE"])
problems=[]
p=ws/"summary.json"
if not p.exists(): problems.append("missing summary.json")
else:
    data=json.loads(p.read_text())
    expected={"books":15.0,"games":35.0,"figures":35.0}
    if data != expected: problems.append(f"expected {expected}, got {data}")
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
