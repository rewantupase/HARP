"""MCP tool: retrieve chat history."""
from __future__ import annotations


async def chat_history_lookup(thread_id: str, limit: int = 20) -> list[dict]:
    """Retrieve recent messages for a chat thread."""
    from uuid import UUID
    from app.database.session import get_session
    from app.database.models.conversation import Conversation
    from app.database.memory import get_recent_messages
    with get_session() as session:
        conv = session.query(Conversation).filter_by(thread_id=UUID(thread_id)).first()
        if conv is None:
            return []
        messages = get_recent_messages(session, conv.id, limit=limit)
    return [{"id": str(m.id), "role": m.role, "content": m.content,
             "model_used": m.model_used, "created_at": str(m.created_at)} for m in messages]
