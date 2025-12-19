import json
from pathlib import Path
from typing import Any


SAVE_PATH = Path("data") / "save.json"


def load_save() -> dict[str, Any]:
    if not SAVE_PATH.exists():
        return {"player": {"name": "Explorateur", "level": 1, "artifacts": 0, "rooms_unlocked": 1}}

    with SAVE_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_save(data: dict[str, Any]) -> None:
    SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SAVE_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
