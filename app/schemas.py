from __future__ import annotations

from pydantic import BaseModel, Field, AnyUrl
from typing import Optional

# ========= AUTH =========
class LoginReq(BaseModel):
    username: str
    password: str

class LoginResp(BaseModel):
    token: str


# ========= POSKO =========
class PoskoCreate(BaseModel):
    nama: str = Field(min_length=2)
    alamat: str = Field(min_length=3)
    lat: float
    lng: float
    kapasitas: Optional[int] = None
    telepon: Optional[str] = None
    keterangan: Optional[str] = None

class PoskoUpdate(BaseModel):
    nama: Optional[str] = None
    alamat: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    kapasitas: Optional[int] = None
    telepon: Optional[str] = None
    keterangan: Optional[str] = None

class PoskoOut(BaseModel):
    id: str
    nama: str
    alamat: str
    lat: float
    lng: float
    kapasitas: Optional[int] = None
    telepon: Optional[str] = None
    keterangan: Optional[str] = None
    created_at: str
    updated_at: str


# ========= VIDEO =========
class VideoCreate(BaseModel):
    judul: str = Field(min_length=2)
    url: AnyUrl
    keterangan: Optional[str] = None

class VideoUpdate(BaseModel):
    judul: Optional[str] = None
    url: Optional[AnyUrl] = None
    keterangan: Optional[str] = None

class VideoOut(BaseModel):
    id: str
    judul: str
    url: str
    keterangan: Optional[str] = None
    created_at: str
    updated_at: str
