import json, os, subprocess, sys
from pathlib import Path
ws = Path(os.environ["WORKSPACE"])
proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "test_wordcount.py"], cwd=ws, capture_output=True, text=True, timeout=120)
print(json.dumps({"passed": proc.returncode == 0, "reason": (proc.stdout or "")[-800:] + (proc.stderr or "")[-400:], "score": 1.0 if proc.returncode == 0 else 0.0}))
