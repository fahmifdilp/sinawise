from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from .db import get_session
from .models import Posko, PoskoCreate, PoskoUpdate, PoskoOut
from .auth import require_admin

router = APIRouter(tags=["posko"])


def now_utc():
    return datetime.now(timezone.utc)


# ===== PUBLIC =====
@router.get("/evacuation/posts", response_model=List[PoskoOut])
def public_list_posko(session: Session = Depends(get_session)):
    rows = session.exec(select(Posko).order_by(Posko.created_at.desc())).all()
    return rows


# ===== ADMIN =====
@router.get("/admin/posts", response_model=List[PoskoOut])
def admin_list_posko(
    session: Session = Depends(get_session),
    user: str = Depends(require_admin),
):
    rows = session.exec(select(Posko).order_by(Posko.created_at.desc())).all()
    return rows


@router.post("/admin/posts", response_model=PoskoOut)
def admin_create_posko(
    payload: PoskoCreate,
    session: Session = Depends(get_session),
    user: str = Depends(require_admin),
):
    item = Posko(**payload.model_dump())
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/admin/posts/{posko_id}", response_model=PoskoOut)
def admin_update_posko(
    posko_id: str,
    payload: PoskoUpdate,
    session: Session = Depends(get_session),
    user: str = Depends(require_admin),
):
    item = session.get(Posko, posko_id)
    if not item:
        raise HTTPException(status_code=404, detail="Posko not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(item, k, v)
    item.updated_at = now_utc()

    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/admin/posts/{posko_id}")
def admin_delete_posko(
    posko_id: str,
    session: Session = Depends(get_session),
    user: str = Depends(require_admin),
):
    item = session.get(Posko, posko_id)
    if not item:
        raise HTTPException(status_code=404, detail="Posko not found")

    session.delete(item)
    session.commit()
    return {"ok": True}
