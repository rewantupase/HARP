from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class ConversationSummary(Base):
    __tablename__ = "conversation_summaries"
    __table_args__ = (Index("ix_conv_summaries_conv_id", "conversation_id"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    covers_up_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("conversation_messages.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    conversation: Mapped["Conversation"] = relationship(back_populates="summaries")


from app.database.models.conversation import Conversation  # noqa: E402
