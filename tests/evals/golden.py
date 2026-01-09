from __future__ import annotations

import difflib
from pathlib import Path


def golden_dir() -> Path:
    """Return the directory containing golden snapshot files."""
    return Path(__file__).resolve().parent / "golden_snapshots"


def read_golden(name: str) -> str:
    """Read a golden snapshot by name."""
    path = golden_dir() / f"{name}.txt"
    return path.read_text(encoding="utf-8")


def assert_golden(*, name: str, actual: str) -> None:
    """Assert actual text equals the golden snapshot, showing a unified diff on failure."""
    expected = read_golden(name).rstrip()
    normalized_actual = actual.rstrip()
    if normalized_actual == expected:
        return

    diff = "\n".join(
        difflib.unified_diff(
            expected.splitlines(),
            normalized_actual.splitlines(),
            fromfile=f"expected:{name}",
            tofile=f"actual:{name}",
            lineterm="",
        )
    )
    raise AssertionError(f"Golden snapshot mismatch for {name}:\n{diff}")


