import json, os
from pathlib import Path
ws = Path(os.environ["WORKSPACE"])
p = ws / "answers.md"
problems = []
if not p.exists():
    problems.append("missing answers.md")
else:
    text = p.read_text().lower()
    for needle in ["mara", "shorted battery", "18 minutes"]:
        if needle not in text:
            problems.append("missing " + needle)
    for incident in ["incident 12", "incident 22", "incident 19"]:
        if incident not in text:
            problems.append("missing citation " + incident)
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
