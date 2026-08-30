import json, os
from pathlib import Path
ws = Path(os.environ["WORKSPACE"])
p = ws / "urls.txt"
problems = []
if not p.exists():
    problems.append("missing urls.txt")
else:
    lines = p.read_text().splitlines()
    expected = ["https://example.com/a", "https://example.com/b", "https://example.com/c"]
    if lines != expected:
        problems.append(f"expected {expected}, got {lines}")
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
