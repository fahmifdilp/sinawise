from __future__ import annotations

from dataclasses import dataclass

from .storage import read_json, write_json

STATE_KEY = "scheduler_state"


@dataclass
class State:
    last_report_id: str | None = None
    last_level: str | None = None


def load_state() -> State:
    data = read_json(STATE_KEY, {})
    if not isinstance(data, dict):
        return State()
    return State(
        last_report_id=data.get("last_report_id"),
        last_level=data.get("last_level"),
    )


def save_state(state: State) -> None:
    payload = {
        "last_report_id": state.last_report_id,
        "last_level": state.last_level,
    }
    write_json(STATE_KEY, payload)
