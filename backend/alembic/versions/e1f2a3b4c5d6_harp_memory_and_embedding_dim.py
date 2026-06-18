"""HARP: memory tables and 384-dim embeddings

Revision ID: e1f2a3b4c5d6
Revises: d2e4b7a9c1f3
Create Date: 2026-06-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e1f2a3b4c5d6"
down_revision = "d2e4b7a9c1f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Resize embedding column to 384-dim (bge-small-en-v1.5)
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(384) USING NULL")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding")
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding ON document_chunks "
        "USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)"
    )

    # 2. conversations
    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chat_threads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_conversations_thread_id", "conversations", ["thread_id"])
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])

    # 3. conversation_messages
    op.create_table(
        "conversation_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("model_used", sa.String(64)),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("token_count", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_conv_messages_conv_id", "conversation_messages", ["conversation_id"])

    # 4. conversation_summaries
    op.create_table(
        "conversation_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("summary_text", sa.Text, nullable=False),
        sa.Column("covers_up_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversation_messages.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_conv_summaries_conv_id", "conversation_summaries", ["conversation_id"])

    # 5. Routing diagnostics columns on chat_messages
    op.add_column("chat_messages", sa.Column("model_used", sa.String(64), nullable=True))
    op.add_column("chat_messages", sa.Column("router_tier", sa.String(16), nullable=True))
    op.add_column("chat_messages", sa.Column("latency_ms", sa.Integer, nullable=True))
    op.add_column("chat_messages", sa.Column("rerank_score", sa.Float, nullable=True))


def downgrade() -> None:
    op.drop_column("chat_messages", "rerank_score")
    op.drop_column("chat_messages", "latency_ms")
    op.drop_column("chat_messages", "router_tier")
    op.drop_column("chat_messages", "model_used")
    op.drop_table("conversation_summaries")
    op.drop_table("conversation_messages")
    op.drop_table("conversations")
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1536) USING NULL")
