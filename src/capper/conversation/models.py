"""Conversation storage.

The transcript (`messages`) is what the user saw; `model_messages` is the
model's history; `summaries` record compactions by watermark. All three are
append-only.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from capper.db import Base, UtcDateTime

TURN_IN_PROGRESS = "in_progress"
TURN_COMPLETE = "complete"
TURN_STOPPED = "stopped"
TURN_ERROR = "error"


class Turn(Base):
    __tablename__ = "turns"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_turns_user_idempotency_key"),
        Index(
            "uq_turns_one_in_progress",
            "user_id",
            unique=True,
            sqlite_where=text("status = 'in_progress'"),
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"), index=True)
    status: Mapped[str] = mapped_column(String)
    idempotency_key: Mapped[str] = mapped_column(String)
    request_text_hash: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    content_version: Mapped[str] = mapped_column(String)
    app_version: Mapped[str] = mapped_column(String)
    started_at: Mapped[datetime] = mapped_column(UtcDateTime)
    ended_at: Mapped[datetime | None] = mapped_column(UtcDateTime)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"), index=True)
    turn_id: Mapped[str] = mapped_column(ForeignKey("turns.id"), index=True)
    role: Mapped[str] = mapped_column(String)
    parts: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime)


class ModelMessageRow(Base):
    __tablename__ = "model_messages"
    __table_args__ = (Index("ix_model_messages_user_seq", "user_id", "id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"))
    turn_id: Mapped[str] = mapped_column(ForeignKey("turns.id"), index=True)
    seq: Mapped[int] = mapped_column(Integer)
    payload: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime)


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"), index=True)
    covers_through_model_message_id: Mapped[int] = mapped_column(ForeignKey("model_messages.id"))
    text: Mapped[str] = mapped_column(String)
    payload: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    content_version: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime)


class ToolCallRecord(Base):
    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"), index=True)
    turn_id: Mapped[str] = mapped_column(ForeignKey("turns.id"), index=True)
    tool_name: Mapped[str] = mapped_column(String)
    arguments: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String)
    latency_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime)


class MessageFeedback(Base):
    __tablename__ = "message_feedback"
    __table_args__ = (UniqueConstraint("user_id", "message_id", name="uq_feedback_user_message"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"))
    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"))
    rating: Mapped[str] = mapped_column(String)
    comment: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime)
