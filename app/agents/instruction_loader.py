"""Load the Markdown instructions used by the agent implementations."""

from functools import lru_cache
from pathlib import Path

INSTRUCTIONS_DIR = Path(__file__).parents[1] / "prompts"


@lru_cache(maxsize=None)
def load_agent_instructions(filename: str) -> str:
    path = (INSTRUCTIONS_DIR / filename).resolve()
    if path.parent != INSTRUCTIONS_DIR.resolve():
        raise ValueError("Instruction file must be inside the instructions directory")
    return path.read_text(encoding="utf-8").strip()
