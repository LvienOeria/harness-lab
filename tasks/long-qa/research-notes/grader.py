import json, os
from pathlib import Path
ws = Path(os.environ["WORKSPACE"])
p = ws / "answers.md"
problems = []
if not p.exists():
    problems.append("missing answers.md")
else:
    text = p.read_text().lower()
    for needle in ["crystalline lattice", "2087", "notes_a", "notes_b"]:
        if needle not in text:
            problems.append("missing " + needle)
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
