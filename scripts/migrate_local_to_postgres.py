from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.models import AppKV, Posko, Video

DATA_DIR = BASE_DIR / "data"
SOURCE_DATABASE_URL = os.getenv("SOURCE_DATABASE_URL", f"sqlite:///{(BASE_DIR / 'sinawise.db').as_posix()}")
TARGET_DATABASE_URL = os.getenv("TARGET_DATABASE_URL") or os.getenv("DATABASE_URL", "")


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _upsert_kv(session: Session, key: str, value) -> None:
    item = session.get(AppKV, key)
    payload = json.dumps(value, ensure_ascii=False, indent=2)
    if item is None:
        item = AppKV(key=key, value_json=payload)
    else:
        item.value_json = payload
    session.add(item)


def _migrate_sql_table(source_session: Session, target_session: Session, model) -> int:
    rows = source_session.exec(select(model)).all()
    count = 0
    for row in rows:
        existing = target_session.get(model, row.id)
        payload = row.model_dump()
        if existing is None:
            target_session.add(model(**payload))
        else:
            for field_name, value in payload.items():
                setattr(existing, field_name, value)
            target_session.add(existing)
        count += 1
    return count


def main() -> None:
    if not TARGET_DATABASE_URL:
        raise SystemExit("Set TARGET_DATABASE_URL atau DATABASE_URL ke koneksi Postgres target.")

    source_engine = create_engine(SOURCE_DATABASE_URL, connect_args={"check_same_thread": False})
    target_engine = create_engine(TARGET_DATABASE_URL)
    SQLModel.metadata.create_all(target_engine)

    migrated_counts: dict[str, int] = {
        "posko": 0,
        "video": 0,
        "kv": 0,
    }

    with Session(source_engine) as source_session, Session(target_engine) as target_session:
        migrated_counts["posko"] = _migrate_sql_table(source_session, target_session, Posko)
        migrated_counts["video"] = _migrate_sql_table(source_session, target_session, Video)

        for json_file in sorted(DATA_DIR.glob("*.json")):
            value = _load_json(json_file)
            if value is None:
                continue
            _upsert_kv(target_session, json_file.stem, value)
            migrated_counts["kv"] += 1

        legacy_state = BASE_DIR / "state.json"
        if legacy_state.exists():
            value = _load_json(legacy_state)
            if value is not None:
                _upsert_kv(target_session, "scheduler_state", value)
                migrated_counts["kv"] += 1

        target_session.commit()

    print("Migrasi selesai.")
    print(f"Posko  : {migrated_counts['posko']}")
    print(f"Video  : {migrated_counts['video']}")
    print(f"State  : {migrated_counts['kv']}")


if __name__ == "__main__":
    main()
