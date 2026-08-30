import json, os
from pathlib import Path
ws=Path(os.environ["WORKSPACE"])
p=ws/"answers.md"
problems=[]
if not p.exists(): problems.append("missing answers.md")
else:
 t=p.read_text().lower()
 for needle in ["40 percent","airlock 2","m-77","section"]:
  if needle not in t: problems.append("missing "+needle)
print(json.dumps({"passed": not problems,"reason":"; ".join(problems) or "ok","score":1.0 if not problems else 0.0}))
