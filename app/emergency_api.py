from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Session, select

from .db import get_session
from .admin_auth_api import admin_guard


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
router = APIRouter(prefix="/emergency", tags=["Emergency"])

admin_router = APIRouter(
    prefix="/admin/emergency",
    tags=["Admin Emergency"],
    dependencies=[Depends(admin_guard)],
)


def _get_or_create(session: Session) -> EmergencyState:
    st = session.exec(select(EmergencyState).where(EmergencyState.id == 1)).first()
    if st is None:
        st = EmergencyState(id=1)
        session.add(st)
        session.commit()
        session.refresh(st)
    return st


@router.get("/status")
def status(session: Session = Depends(get_session)):
    st = _get_or_create(session)
    return {
        "active": st.active,
        "level": st.level,
        "message": st.message,
        "updated_at": st.updated_at,
    }


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
    return {"ok": True, "status": {"active": st.active, "level": st.level, "message": st.message, "updated_at": st.updated_at}}


# ✅ alias biar /activate juga bisa (biar gak 404 lagi)
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
    return {"ok": True, "status": {"active": st.active, "level": st.level, "message": st.message, "updated_at": st.updated_at}}
