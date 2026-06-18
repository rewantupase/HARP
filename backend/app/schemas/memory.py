from __future__ import annotations
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class MemoryMessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    model_used: str | None
    created_at: datetime


class MemoryOut(BaseModel):
    summary: str | None
    messages: list[MemoryMessageOut]
