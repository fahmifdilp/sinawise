from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .admin_auth_api import admin_guard

router = APIRouter(tags=["emergency"])

# Ambil send_to_topic dari notifier (kalau tersedia)
try:
    from .notifier import send_to_topic
except Exception:
    send_to_topic = None

EMERGENCY_TOPIC = os.environ.get("FCM_EMERGENCY_TOPIC", "sinabung_emergency").strip() or "sinabung_emergency"

class EmergencyReq(BaseModel):
    kind: str = Field(..., description="alarm atau stop")
    title: Optional[str] = None
    body: Optional[str] = None

@router.post("/admin/emergency/trigger", dependencies=[Depends(admin_guard)])
def emergency_trigger(payload: EmergencyReq) -> Dict[str, Any]:
    if send_to_topic is None:
        raise HTTPException(status_code=503, detail="FCM notifier belum siap (cek notifier.py & credentials).")

    kind = payload.kind.strip().lower()
    if kind not in ("alarm", "stop"):
        raise HTTPException(status_code=400, detail="kind harus 'alarm' atau 'stop'")

    title = payload.title or ("PERINGATAN DARURAT" if kind == "alarm" else "STOP PERINGATAN")
    body = payload.body or ("Segera menuju posko terdekat!" if kind == "alarm" else "Peringatan dihentikan.")

    # Data penting untuk aplikasi flutter (nanti flutter baca ini)
    data = {
        "type": "EMERGENCY_ALARM" if kind == "alarm" else "EMERGENCY_STOP",
        "ts_utc": datetime.now(timezone.utc).isoformat(),
    }

    msg_id = send_to_topic(
        topic=EMERGENCY_TOPIC,
        title=title,
        body=body,
        data=data,
    )

    return {"ok": True, "topic": EMERGENCY_TOPIC, "message_id": str(msg_id), "data": data}
