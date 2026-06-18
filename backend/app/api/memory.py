"""Memory API endpoints."""
from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.database.session import get_session
from app.database.memory import (get_or_create_conversation, get_recent_messages, get_latest_summary)
from app.database.models.user import User
from app.schemas.memory import MemoryOut, MemoryMessageOut

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/{thread_id}", response_model=MemoryOut)
async def get_memory(thread_id: UUID, current_user: User = Depends(get_current_user)):
    with get_session() as session:
        conv = get_or_create_conversation(session, thread_id, current_user.id)
        session.commit()
        summary_obj = get_latest_summary(session, conv.id)
        messages = get_recent_messages(session, conv.id, limit=20)
        return MemoryOut(
            summary=summary_obj.summary_text if summary_obj else None,
            messages=[MemoryMessageOut(id=m.id, role=m.role, content=m.content,
                                       model_used=m.model_used, created_at=m.created_at)
                      for m in messages],
        )
