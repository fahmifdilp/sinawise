from __future__ import annotations

import os
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Session, select

from .db import get_session
from .admin_auth_api import admin_guard

logger = logging.getLogger("sinabung")

# Optional: FCM notifier (kalau firebase_admin belum siap, endpoint tetap jalan)
try:
    from .notifier import send_to_topic  # send_to_topic(topic, title, body, data)
except Exception as e:
    send_to_topic = None
    logger.warning("FCM notifier not ready: %s: %s", type(e).__name__, e)


# =========================
# DB MODEL
# =========================
class EmergencyState(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    active: bool = Field(default=False)
    level: Optional[str] = Field(default=None)
    message: str = Field(default="Peringatan darurat.")
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# =========================
# REQUEST BODY
# =========================
class TriggerReq(BaseModel):
    level: str = "AWAS"
    message: str = "Peringatan darurat."


class ClearReq(BaseModel):
    message: str = "Situasi sudah aman."


# =========================
# ROUTERS
# =========================
# router utama yang akan di-include di main.py
router = APIRouter()

public_router = APIRouter(prefix="/emergency", tags=["Emergency"])

admin_router = APIRouter(
    prefix="/admin/emergency",
    tags=["Admin Emergency"],
    dependencies=[Depends(admin_guard)],
)

# gabungkan semua endpoint
router.include_router(public_router)
router.include_router(admin_router)


def _get_or_create(session: Session) -> EmergencyState:
    st = session.exec(select(EmergencyState).where(EmergencyState.id == 1)).first()
    if st is None:
        st = EmergencyState(id=1)
        session.add(st)
        session.commit()
        session.refresh(st)
    return st


def _topic() -> str:
    # pakai env kalau ada, fallback ke "sinabung"
    return (os.getenv("FCM_TOPIC", "sinabung").strip() or "sinabung")


def _send_emergency_push(st: EmergencyState) -> None:
    """
    Kirim push ke semua user (topic).
    - Trigger: notifikasi BAHAYA
    - Clear: bisa opsional (default: tidak kirim)
    """
    if send_to_topic is None:
        logger.info("FCM disabled (send_to_topic not available).")
        return

    # kalau clear, default tidak kirim notif biar nggak spam
    notify_clear = os.getenv("EMERGENCY_NOTIFY_CLEAR", "0").strip() == "1"
    if (not st.active) and (not notify_clear):
        return

    level = st.level or ""
    if st.active:
        title = f"BAHAYA{(' - ' + level) if level else ''}"
        body = st.message or "Segera evakuasi!"
    else:
        title = "INFO"
        body = st.message or "Situasi sudah aman."

    data = {
        "event": "emergency",
        "route": "/emergency",  # Flutter buka ke halaman emergency
        "active": "true" if st.active else "false",
        "level": level,
        "message": st.message or "",
        "updated_at": st.updated_at,
    }

    try:
        msg_id = send_to_topic(topic=_topic(), title=title, body=body, data=data)
        logger.info("FCM sent msg_id=%s topic=%s active=%s", msg_id, _topic(), st.active)
    except Exception:
        logger.exception("Failed to send FCM (cek GOOGLE_APPLICATION_CREDENTIALS / firebase).")


# =========================
# PUBLIC
# =========================
@public_router.get("/status")
def status(session: Session = Depends(get_session)):
    st = _get_or_create(session)
    return {
        "active": st.active,
        "level": st.level,
        "message": st.message,
        "updated_at": st.updated_at,
    }


# =========================
# ADMIN
# =========================
@admin_router.post("/trigger")
def trigger(req: TriggerReq, session: Session = Depends(get_session)):
    st = _get_or_create(session)
    st.active = True
    st.level = req.level
    st.message = req.message
    st.updated_at = datetime.now(timezone.utc).isoformat()

    session.add(st)
    session.commit()
    session.refresh(st)

    # ✅ kirim push saat emergency ON
    _send_emergency_push(st)

    return {
        "ok": True,
        "status": {
            "active": st.active,
            "level": st.level,
            "message": st.message,
            "updated_at": st.updated_at,
        },
    }


# ✅ alias biar /activate juga bisa
@admin_router.post("/activate")
def activate(req: TriggerReq, session: Session = Depends(get_session)):
    return trigger(req, session)


@admin_router.post("/clear")
def clear(req: Optional[ClearReq] = None, session: Session = Depends(get_session)):
    st = _get_or_create(session)

    st.active = False
    st.level = None
    st.message = req.message if req else "Situasi sudah aman."
    st.updated_at = datetime.now(timezone.utc).isoformat()

    session.add(st)
    session.commit()
    session.refresh(st)

    # (opsional) kirim push saat aman kalau EMERGENCY_NOTIFY_CLEAR=1
    _send_emergency_push(st)

    return {
        "ok": True,
        "status": {
            "active": st.active,
            "level": st.level,
            "message": st.message,
            "updated_at": st.updated_at,
        },
    }
