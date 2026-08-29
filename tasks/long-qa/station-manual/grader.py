import json, os, re
from pathlib import Path
ws=Path(os.environ["WORKSPACE"])
p=ws/"answers.md"
problems=[]
if not p.exists(): problems.append("missing answers.md")
else:
    text=p.read_text().lower()
    checks={"90 minutes":"90 minutes","b":"airlock b","7.4 ghz":"7.4 ghz"}
    for key, needle in checks.items():
        if needle not in text: problems.append(f"answer missing for {key}")
    if "section 1" not in text: problems.append("missing Section 1 citation")
    if "section 3" not in text: problems.append("missing Section 3 citation")
    if "section 4" not in text: problems.append("missing Section 4 citation")
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
