import json, os
from pathlib import Path
ws = Path(os.environ["WORKSPACE"])
expected = {
    "text/notes.txt": "hello from notes\n",
    "text/report.md": "# Report\n",
    "data/data.csv": "a,b\n1,2\n",
    "data/config.json": '{"k": 1}\n',
}
problems = []
for rel, content in expected.items():
    p = ws / rel
    if not p.exists():
        problems.append(f"missing {rel}")
    elif p.read_text() != content:
        problems.append(f"content mismatch {rel}")
extra = sorted(str(p.relative_to(ws)) for p in ws.rglob('*') if p.is_file() and p.relative_to(ws).as_posix() not in expected)
if extra:
    problems.append(f"unexpected files: {extra}")
if (ws/'incoming').exists() and any((ws/'incoming').iterdir()):
    problems.append("incoming directory still contains files")
print(json.dumps({"passed": not problems, "reason": "; ".join(problems) or "ok", "score": 1.0 if not problems else 0.0}))
