from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .storage import read_json, write_json

router = APIRouter(tags=["iot"])
logger = logging.getLogger("sinabung.iot")

STATE_KEY = "air_quality_state"

IOT_API_KEY = os.environ.get("IOT_API_KEY", "").strip()
PM25_GREEN_MAX = float(os.environ.get("IOT_PM25_GREEN_MAX", "15"))
PM25_YELLOW_MAX = float(os.environ.get("IOT_PM25_YELLOW_MAX", "35"))


class AirPayload(BaseModel):
    pm25: float = Field(..., description="PM2.5 ug/m3")
    pm10: Optional[float] = Field(None, description="PM10 ug/m3")
    pm1: Optional[float] = Field(None, description="PM1.0 ug/m3")
    device_id: Optional[str] = Field(None, description="ID device")


def _default_state() -> Dict[str, Any]:
    return {
        "pm25": None,
        "pm10": None,
        "pm1": None,
        "status": "unknown",
        "label": "tidak diketahui",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "device_id": None,
    }


def _load_state() -> Dict[str, Any]:
    data = read_json(STATE_KEY, _default_state())
    if not isinstance(data, dict):
        data = _default_state()
    data.setdefault("pm25", None)
    data.setdefault("pm10", None)
    data.setdefault("pm1", None)
    data.setdefault("status", "unknown")
    data.setdefault("label", "tidak diketahui")
    data.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
    data.setdefault("device_id", None)
    return data


def _save_state(state: Dict[str, Any]) -> None:
    write_json(STATE_KEY, state)


def _pm25_status(pm25: float) -> Dict[str, str]:
    if pm25 <= PM25_GREEN_MAX:
        return {"status": "green", "label": "aman"}
    if pm25 <= PM25_YELLOW_MAX:
        return {"status": "yellow", "label": "waspada"}
    return {"status": "red", "label": "bahaya"}


def _check_api_key(request: Request) -> None:
    if not IOT_API_KEY:
        return
    key = request.headers.get("X-IOT-KEY", "").strip()
    if key != IOT_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid IOT API key")


@router.get("/iot/air/latest")
def air_latest() -> Dict[str, Any]:
    return _load_state()


@router.post("/iot/air")
def air_ingest(payload: AirPayload, request: Request) -> Dict[str, Any]:
    _check_api_key(request)

    status = _pm25_status(payload.pm25)
    state = _load_state()
    state.update(
        {
            "pm25": float(payload.pm25),
            "pm10": float(payload.pm10) if payload.pm10 is not None else None,
            "pm1": float(payload.pm1) if payload.pm1 is not None else None,
            "status": status["status"],
            "label": status["label"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "device_id": payload.device_id,
        }
    )
    _save_state(state)
    logger.info("Air quality updated pm25=%s status=%s", state["pm25"], state["status"])
    return {"ok": True, "status": state}
