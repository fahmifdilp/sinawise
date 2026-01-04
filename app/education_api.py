from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from .db import get_session
from .models import Video, VideoCreate, VideoUpdate, VideoOut
from .auth import require_admin

router = APIRouter(tags=["education"])


def now_utc():
    return datetime.now(timezone.utc)


# ===== PUBLIC =====
@router.get("/education/videos", response_model=List[VideoOut])
def public_list_videos(session: Session = Depends(get_session)):
    rows = session.exec(select(Video).order_by(Video.created_at.desc())).all()
    return rows


# ===== ADMIN =====
@router.get("/admin/videos", response_model=List[VideoOut])
def admin_list_videos(
    session: Session = Depends(get_session),
    user: str = Depends(require_admin),
):
    rows = session.exec(select(Video).order_by(Video.created_at.desc())).all()
    return rows


@router.post("/admin/videos", response_model=VideoOut)
def admin_create_video(
    payload: VideoCreate,
    session: Session = Depends(get_session),
    user: str = Depends(require_admin),
):
    item = Video(**payload.model_dump())
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/admin/videos/{video_id}", response_model=VideoOut)
def admin_update_video(
    video_id: str,
    payload: VideoUpdate,
    session: Session = Depends(get_session),
    user: str = Depends(require_admin),
):
    item = session.get(Video, video_id)
    if not item:
        raise HTTPException(status_code=404, detail="Video not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(item, k, v)
    item.updated_at = now_utc()

    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/admin/videos/{video_id}")
def admin_delete_video(
    video_id: str,
    session: Session = Depends(get_session),
    user: str = Depends(require_admin),
):
    item = session.get(Video, video_id)
    if not item:
        raise HTTPException(status_code=404, detail="Video not found")

    session.delete(item)
    session.commit()
    return {"ok": True}
