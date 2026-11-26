"""Capper's tables on top of the supplied database.

Adds `Products.image_url` and `Users.time_zone`, creates every table the
service owns (including the FTS5 history index and the partial unique indexes),
and drops the supplied legacy `Conversation_History` table, which Capper's own
conversation tables replace. The downgrade recreates that table empty, with its
original schema; the legacy rows aren't restored.

Revision ID: 0001
Revises:
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TIMESTAMP = sa.String  # UTC ISO 8601 text (capper.db.UtcDateTime)


def upgrade() -> None:
    # Native ALTER keeps the supplied schema (AUTOINCREMENT) intact; a batch rebuild wouldn't.
    op.execute("ALTER TABLE Products ADD COLUMN image_url TEXT")
    op.execute("ALTER TABLE Users ADD COLUMN time_zone TEXT")

    op.drop_table("Conversation_History")

    op.create_table(
        "referral_codes",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("Users.id"), primary_key=True),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("created_at", TIMESTAMP(), nullable=False),
    )
    op.create_table(
        "promotions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("Products.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("starts_at", TIMESTAMP(), nullable=False),
        sa.Column("ends_at", TIMESTAMP(), nullable=False),
    )
    op.create_table(
        "guidance_notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("Users.id"), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("expires_at", TIMESTAMP(), nullable=True),
        sa.Column("created_at", TIMESTAMP(), nullable=False),
        sa.Column("updated_at", TIMESTAMP(), nullable=False),
    )
    op.create_index("ix_guidance_notes_user_id", "guidance_notes", ["user_id"])
    op.create_table(
        "avoided_products",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("Users.id"), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("Products.id"), primary_key=True),
        sa.Column("created_at", TIMESTAMP(), nullable=False),
    )
    op.create_table(
        "content_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("content_class", sa.String(), nullable=False),
        sa.Column("load", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("ingested_at", sa.String(), nullable=False),
    )
    op.create_index(
        "uq_content_documents_active_name",
        "content_documents",
        ["name"],
        unique=True,
        sqlite_where=sa.text("active = 1"),
    )
    op.create_table(
        "turns",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("Users.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("request_text_hash", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("content_version", sa.String(), nullable=False),
        sa.Column("app_version", sa.String(), nullable=False),
        sa.Column("started_at", TIMESTAMP(), nullable=False),
        sa.Column("ended_at", TIMESTAMP(), nullable=True),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_turns_user_idempotency_key"),
    )
    op.create_index("ix_turns_user_id", "turns", ["user_id"])
    op.create_index(
        "uq_turns_one_in_progress",
        "turns",
        ["user_id"],
        unique=True,
        sqlite_where=sa.text("status = 'in_progress'"),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("Users.id"), nullable=False),
        sa.Column("turn_id", sa.String(), sa.ForeignKey("turns.id"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("parts", sa.JSON(), nullable=False),
        sa.Column("created_at", TIMESTAMP(), nullable=False),
    )
    op.create_index("ix_messages_user_id", "messages", ["user_id"])
    op.create_index("ix_messages_turn_id", "messages", ["turn_id"])
    op.execute(
        "CREATE VIRTUAL TABLE messages_fts USING fts5("
        "text, user_id UNINDEXED, message_id UNINDEXED, tokenize = 'porter unicode61')"
    )
    op.create_table(
        "model_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("Users.id"), nullable=False),
        sa.Column("turn_id", sa.String(), sa.ForeignKey("turns.id"), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("payload", sa.String(), nullable=False),
        sa.Column("created_at", TIMESTAMP(), nullable=False),
    )
    op.create_index("ix_model_messages_user_seq", "model_messages", ["user_id", "id"])
    op.create_index("ix_model_messages_turn_id", "model_messages", ["turn_id"])
    op.create_table(
        "summaries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("Users.id"), nullable=False),
        sa.Column(
            "covers_through_model_message_id",
            sa.Integer(),
            sa.ForeignKey("model_messages.id"),
            nullable=False,
        ),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("payload", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("content_version", sa.String(), nullable=False),
        sa.Column("created_at", TIMESTAMP(), nullable=False),
    )
    op.create_index("ix_summaries_user_id", "summaries", ["user_id"])
    op.create_table(
        "tool_calls",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("Users.id"), nullable=False),
        sa.Column("turn_id", sa.String(), sa.ForeignKey("turns.id"), nullable=False),
        sa.Column("tool_name", sa.String(), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", TIMESTAMP(), nullable=False),
    )
    op.create_index("ix_tool_calls_user_id", "tool_calls", ["user_id"])
    op.create_index("ix_tool_calls_turn_id", "tool_calls", ["turn_id"])
    op.create_table(
        "message_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("Users.id"), nullable=False),
        sa.Column("message_id", sa.String(), sa.ForeignKey("messages.id"), nullable=False),
        sa.Column("rating", sa.String(), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("created_at", TIMESTAMP(), nullable=False),
        sa.Column("updated_at", TIMESTAMP(), nullable=False),
        sa.UniqueConstraint("user_id", "message_id", name="uq_feedback_user_message"),
    )


def downgrade() -> None:
    op.drop_table("message_feedback")
    op.drop_table("tool_calls")
    op.drop_table("summaries")
    op.drop_table("model_messages")
    op.execute("DROP TABLE messages_fts")
    op.drop_table("messages")
    op.drop_table("turns")
    op.drop_table("content_documents")
    op.drop_table("avoided_products")
    op.drop_table("guidance_notes")
    op.drop_table("promotions")
    op.drop_table("referral_codes")
    op.create_table(
        "Conversation_History",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("Users.id"), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("sender", sa.Text(), sa.CheckConstraint("sender IN ('user', 'bot')")),
        sa.Column("timestamp", sa.Text(), nullable=False),
        sqlite_autoincrement=True,
    )
    op.execute("ALTER TABLE Products DROP COLUMN image_url")
    op.execute("ALTER TABLE Users DROP COLUMN time_zone")
