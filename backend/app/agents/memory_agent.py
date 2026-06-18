"""Memory agent."""
from __future__ import annotations
from uuid import UUID
import structlog
from app.database.session import get_session
from app.database.memory import (get_or_create_conversation, append_message,
                                   build_memory_context, get_recent_messages, save_summary)

logger = structlog.get_logger()
SUMMARY_THRESHOLD = 20


class MemoryAgent:
    def __init__(self, thread_id: UUID, user_id: UUID) -> None:
        self.thread_id = thread_id
        self.user_id = user_id

    def retrieve(self, query: str) -> str:
        with get_session() as session:
            conv = get_or_create_conversation(session, self.thread_id, self.user_id)
            session.commit()
            context = build_memory_context(session, conv.id)
        logger.info("memory_agent.retrieved", chars=len(context))
        return context

    def append(self, role: str, content: str, model_used: str | None = None, latency_ms: int | None = None) -> None:
        from app.database.models.conversation_message import ConversationMessage
        with get_session() as session:
            conv = get_or_create_conversation(session, self.thread_id, self.user_id)
            msg = append_message(session, conv.id, role=role, content=content,
                                 model_used=model_used, latency_ms=latency_ms)
            total = session.query(ConversationMessage).filter_by(conversation_id=conv.id).count()
            if total % SUMMARY_THRESHOLD == 0:
                self._summarize(session, conv.id, last_msg_id=msg.id)
            session.commit()

    def _summarize(self, session, conversation_id: UUID, last_msg_id: UUID) -> None:
        from app.llms.provider_factory import get_openai
        messages = get_recent_messages(session, conversation_id, limit=SUMMARY_THRESHOLD)
        history = "\n".join(f"{m.role}: {m.content}" for m in messages)
        provider = get_openai()
        resp = provider.generate(f"Summarize this conversation concisely:\n\n{history}",
                                 system="You produce brief, factual summaries of conversations.")
        save_summary(session, conversation_id, resp.text, covers_up_to=last_msg_id)
        logger.info("memory_agent.summarized", conversation_id=str(conversation_id))
