from __future__ import annotations

import json
from pathlib import Path

from ai_assistants.adapters.external_hook import HookRequest, HookResponse


def generate_schema(output_path: Path) -> None:
    """Generate a JSON Schema bundle for the purchases external hook (v1)."""
    bundle = {
        "name": "purchases_hook",
        "version": "v1",
        "request_schema": HookRequest.model_json_schema(),
        "response_schema": HookResponse.model_json_schema(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    """CLI entrypoint."""
    repo_root = Path(__file__).resolve().parents[1]
    output_path = repo_root / "schemas" / "purchases_hook_v1.json"
    generate_schema(output_path)


if __name__ == "__main__":
    main()


