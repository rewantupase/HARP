"""CRUD for conversation memory tables."""
from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session
from app.database.models.conversation import Conversation
from app.database.models.conversation_message import ConversationMessage
from app.database.models.conversation_summary import ConversationSummary

SUMMARY_THRESHOLD = 20


def get_or_create_conversation(session: Session, thread_id: UUID, user_id: UUID) -> Conversation:
    conv = session.query(Conversation).filter_by(thread_id=thread_id).first()
    if conv is None:
        conv = Conversation(thread_id=thread_id, user_id=user_id)
        session.add(conv)
        session.flush()
    return conv


def append_message(session: Session, conversation_id: UUID, role: str, content: str,
                   model_used: str | None = None, latency_ms: int | None = None,
                   token_count: int | None = None) -> ConversationMessage:
    msg = ConversationMessage(conversation_id=conversation_id, role=role, content=content,
                              model_used=model_used, latency_ms=latency_ms, token_count=token_count)
    session.add(msg)
    session.flush()
    return msg


def get_recent_messages(session: Session, conversation_id: UUID, limit: int = 10) -> list[ConversationMessage]:
    return (session.query(ConversationMessage).filter_by(conversation_id=conversation_id)
            .order_by(ConversationMessage.created_at.desc()).limit(limit).all()[::-1])


def get_latest_summary(session: Session, conversation_id: UUID) -> ConversationSummary | None:
    return (session.query(ConversationSummary).filter_by(conversation_id=conversation_id)
            .order_by(ConversationSummary.created_at.desc()).first())


def save_summary(session: Session, conversation_id: UUID, summary_text: str,
                 covers_up_to: UUID | None = None) -> ConversationSummary:
    summary = ConversationSummary(conversation_id=conversation_id, summary_text=summary_text,
                                   covers_up_to=covers_up_to)
    session.add(summary)
    session.flush()
    return summary


def build_memory_context(session: Session, conversation_id: UUID) -> str:
    summary = get_latest_summary(session, conversation_id)
    recent = get_recent_messages(session, conversation_id, limit=10)
    parts: list[str] = []
    if summary:
        parts.append(f"[Conversation summary so far]\n{summary.summary_text}")
    if recent:
        history = "\n".join(f"{m.role.upper()}: {m.content}" for m in recent)
        parts.append(f"[Recent messages]\n{history}")
    return "\n\n".join(parts) if parts else ""
