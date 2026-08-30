from __future__ import annotations

from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2] / "skills"


def load_skill(name: str) -> str:
    path = SKILLS_ROOT / name / "SKILL.md"
    if not path.exists():
        raise FileNotFoundError(f"unknown skill: {name} (looked in {path})")
    return path.read_text(encoding="utf-8").strip()


def inject_skills(system_prompt: str, names: list[str]) -> str:
    blocks = [system_prompt]
    for name in names:
        body = load_skill(name)
        blocks.append(f"\n\n<skill name=\"{name}\">\n{body}\n</skill>")
    return "".join(blocks)
