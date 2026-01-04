from __future__ import annotations

import os
from typing import Generator

from sqlmodel import SQLModel, create_engine, Session

# Default: SQLite file di folder project
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sinawise.db")

# connect_args khusus sqlite biar aman di thread
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    echo=False,              # ubah True kalau mau lihat SQL query di log
    connect_args=connect_args,
)

def init_db() -> None:
    """Create all tables from SQLModel metadata."""
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a DB session."""
    with Session(engine) as session:
        yield session
