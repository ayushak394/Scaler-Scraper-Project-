from pathlib import Path
import json
from typing import Any, Dict

def atomic_write(path: Path, data: str) -> None:
    """
    Write `data` to a temporary file then atomically replace `path`.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(path)

def load_state(path: Path) -> Dict[str, Any]:
    """
    Load JSON state from path. Return empty dict if file missing or malformed.
    """
    if not path.exists():
        return {}
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}

def save_state(path: Path, state: Dict[str, Any]) -> None:
    """
    Atomically write state (dict) into path.
    """
    atomic_write(path, json.dumps(state, indent=2, ensure_ascii=False))
