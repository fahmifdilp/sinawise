from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlmodel import Session

from .db import engine
from .models import AppKV

BASE_DIR = Path(__file__).resolve().parents[1]  # -> backend/
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _path(name: str) -> Path:
    if not name.endswith(".json"):
        name += ".json"
    return DATA_DIR / name


_MISSING = object()


def _read_legacy_json(name: str) -> Any:
    p = _path(name)
    if not p.exists():
        return _MISSING
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return _MISSING


def read_json(name: str, default: Any) -> Any:
    try:
        with Session(engine) as session:
            item = session.get(AppKV, name)
            if item is not None:
                return json.loads(item.value_json)
    except Exception:
        pass

    legacy = _read_legacy_json(name)
    if legacy is _MISSING:
        return default

    try:
        write_json(name, legacy)
    except Exception:
        pass
    return legacy


def write_json(name: str, data: Any) -> None:
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    with Session(engine) as session:
        item = session.get(AppKV, name)
        if item is None:
            item = AppKV(key=name, value_json=payload)
        else:
            item.value_json = payload
            item.updated_at = datetime.now(timezone.utc)
        session.add(item)
        session.commit()
