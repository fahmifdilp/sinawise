from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlmodel import SQLModel, Field


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class PoskoBase(SQLModel):
    nama: str
    alamat: str
    lat: float
    lng: float
    kapasitas: Optional[int] = None
    telepon: Optional[str] = None
    keterangan: Optional[str] = None


class Posko(PoskoBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True, index=True)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class PoskoCreate(PoskoBase):
    pass


class PoskoUpdate(SQLModel):
    nama: Optional[str] = None
    alamat: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    kapasitas: Optional[int] = None
    telepon: Optional[str] = None
    keterangan: Optional[str] = None


class PoskoOut(PoskoBase):
    id: str
    created_at: datetime
    updated_at: datetime


# ---------------- VIDEOS ----------------

class VideoBase(SQLModel):
    judul: str
    url: str
    keterangan: Optional[str] = None


class Video(VideoBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True, index=True)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class VideoCreate(VideoBase):
    pass


class VideoUpdate(SQLModel):
    judul: Optional[str] = None
    url: Optional[str] = None
    keterangan: Optional[str] = None


class VideoOut(VideoBase):
    id: str
    created_at: datetime
    updated_at: datetime
