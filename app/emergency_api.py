from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Session, select

from .db import get_session
from .admin_auth_api import require_admin
from .notifier import send_to_topic

router = APIRouter(tags=["Emergency"])


# ===== DB MODEL =====
class EmergencyState(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    active: bool = Field(default=False)
    message: str = Field(default="Peringatan darurat.")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ===== SCHEMA =====
class EmergencyTriggerIn(BaseModel):
    message: str = "PERINGATAN DARURAT! Segera lakukan evakuasi."
    # optional: level, source, dll
    level: Optional[str] = None


class EmergencyOut(BaseModel):
    active: bool
    message: str
    updated_at: str


def _get_or_create_state(session: Session) -> EmergencyState:
    st = session.get(EmergencyState, 1)
    if st is None:
        st = EmergencyState(id=1, active=False, message="Peringatan darurat.")
        session.add(st)
        session.commit()
        session.refresh(st)
    return st


# ===== PUBLIC: user bisa cek status =====
@router.get("/emergency/status", response_model=EmergencyOut)
def get_emergency_status(session: Session = Depends(get_session)) -> EmergencyOut:
    st = _get_or_create_state(session)
    return EmergencyOut(
        active=st.active,
        message=st.message,
        updated_at=st.updated_at.isoformat(),
    )


# ===== ADMIN: trigger =====
@router.post("/admin/emergency/trigger")
def admin_trigger_emergency(
    payload: EmergencyTriggerIn,
    _admin: str = Depends(require_admin),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    st = _get_or_create_state(session)
    st.active = True
    st.message = payload.message
    st.updated_at = datetime.now(timezone.utc)
    session.add(st)
    session.commit()

    # kirim push ke semua user (topic)
    # IMPORTANT: kirim notification+data, biar muncul walau app background
    send_to_topic(
        topic="sinabung",
        title="PERINGATAN DARURAT",
        body=payload.message,
        data={
            "type": "emergency",
            "active": "1",
            "message": payload.message,
            "level": payload.level or "",
        },
    )

    return {"ok": True, "active": True, "message": payload.message}


# ===== ADMIN: clear =====
@router.post("/admin/emergency/clear")
def admin_clear_emergency(
    _admin: str = Depends(require_admin),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    st = _get_or_create_state(session)
    st.active = False
    st.updated_at = datetime.now(timezone.utc)
    session.add(st)
    session.commit()

    send_to_topic(
        topic="sinabung",
        title="INFO",
        body="Status sudah aman.",
        data={
            "type": "emergency",
            "active": "0",
            "message": "Status sudah aman.",
        },
    )

    return {"ok": True, "active": False}
