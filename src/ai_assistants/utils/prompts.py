from __future__ import annotations

from pathlib import Path


def load_prompt_text(name: str) -> str:
    """Load a prompt text file from src/ai_assistants/prompts/.

    We keep prompts versioned as plain text files to support review, diffing, and evals.
    """
    base = Path(__file__).resolve().parents[1] / "prompts"
    path = base / name
    return path.read_text(encoding="utf-8")


