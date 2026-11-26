"""Conversation queries, each scoped to one user.

The transcript and the model history are append-only; only a turn's status
row changes, and only from `in_progress` to its end state.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import literal, select, text, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession

from capper.conversation.models import (
    TURN_ERROR,
    TURN_IN_PROGRESS,
    Message,
    MessageFeedback,
    ModelMessageRow,
    Summary,
    ToolCallRecord,
    Turn,
)
from capper.db import UtcDateTime, rowcount


async def get_turn(session: AsyncSession, user_id: int, turn_id: str) -> Turn | None:
    return await session.scalar(select(Turn).where(Turn.id == turn_id, Turn.user_id == user_id))


async def find_turn_by_key(session: AsyncSession, user_id: int, key: str) -> Turn | None:
    return await session.scalar(
        select(Turn).where(Turn.user_id == user_id, Turn.idempotency_key == key)
    )


async def active_turn(session: AsyncSession, user_id: int) -> Turn | None:
    return await session.scalar(
        select(Turn).where(Turn.user_id == user_id, Turn.status == TURN_IN_PROGRESS)
    )


async def add_message(session: AsyncSession, message: Message, searchable: str) -> None:
    """Insert a transcript message and its FTS row in the caller's transaction."""
    session.add(message)
    await session.flush()
    if searchable.strip():
        await session.execute(
            text("INSERT INTO messages_fts (text, user_id, message_id) VALUES (:t, :u, :m)"),
            {"t": searchable, "u": message.user_id, "m": message.id},
        )


async def add_model_messages(
    session: AsyncSession, user_id: int, turn_id: str, payloads: list[str], now: datetime
) -> list[int]:
    """Append serialized model messages in order; returns their row IDs."""
    rows = [
        ModelMessageRow(user_id=user_id, turn_id=turn_id, seq=seq, payload=payload, created_at=now)
        for seq, payload in enumerate(payloads)
    ]
    session.add_all(rows)
    await session.flush()
    return [row.id for row in rows]


async def latest_summary(session: AsyncSession, user_id: int) -> Summary | None:
    return await session.scalar(
        select(Summary).where(Summary.user_id == user_id).order_by(Summary.id.desc()).limit(1)
    )


async def model_messages_after(
    session: AsyncSession, user_id: int, watermark: int | None
) -> list[ModelMessageRow]:
    statement = select(ModelMessageRow).where(ModelMessageRow.user_id == user_id)
    if watermark is not None:
        statement = statement.where(ModelMessageRow.id > watermark)
    rows = await session.scalars(statement.order_by(ModelMessageRow.id))
    return list(rows.all())


async def mark_in_progress_as_error(session: AsyncSession, now: datetime) -> int:
    """Startup recovery: no turn can still be running in a fresh process."""
    result = await session.execute(
        update(Turn).where(Turn.status == TURN_IN_PROGRESS).values(status=TURN_ERROR, ended_at=now)
    )
    return rowcount(result)


async def turn_messages(session: AsyncSession, user_id: int, turn_id: str) -> list[Message]:
    rows = await session.scalars(
        select(Message)
        .where(Message.user_id == user_id, Message.turn_id == turn_id)
        .order_by(Message.created_at)
    )
    return list(rows.all())


async def list_messages(
    session: AsyncSession, user_id: int, before: list[Any] | None, limit: int
) -> list[tuple[Message, str]]:
    """Transcript messages newest first, each with its turn's status."""
    statement = (
        select(Message, Turn.status)
        .join(Turn, Turn.id == Message.turn_id)
        .where(Message.user_id == user_id)
    )
    if before is not None:
        statement = statement.where(
            tuple_(Message.created_at, Message.id)
            < tuple_(literal(before[0], UtcDateTime()), before[1])
        )
    rows = await session.execute(
        statement.order_by(Message.created_at.desc(), Message.id.desc()).limit(limit)
    )
    return [(message, status) for message, status in rows]


async def get_message(session: AsyncSession, user_id: int, message_id: str) -> Message | None:
    return await session.scalar(
        select(Message).where(Message.id == message_id, Message.user_id == user_id)
    )


async def search_messages(
    session: AsyncSession,
    user_id: int,
    fts_query: str | None,
    span: tuple[datetime, datetime] | None,
    limit: int,
) -> list[tuple[str, str, str, datetime]]:
    """The user filter, the optional FTS5 match and the optional UTC span `[start, end)`, in one
    query. Matches come best first by bm25; a span alone comes oldest first."""
    conditions = ["f.user_id = :u", "m.user_id = :u"]
    params: dict[str, Any] = {"u": user_id, "n": limit}
    if fts_query is not None:
        conditions.append("messages_fts MATCH :q")
        params["q"] = fts_query
        snippet = "snippet(messages_fts, 0, '', '', '…', 16)"
        order = "bm25(messages_fts)"
    else:
        snippet = (
            "CASE WHEN length(f.text) > 160 THEN substr(f.text, 1, 160) || '…' ELSE f.text END"
        )
        order = "m.created_at, m.id"
    if span is not None:
        # Stored timestamps are UTC ISO 8601 text (`UtcDateTime`), so they compare as text.
        conditions += ["m.created_at >= :start", "m.created_at < :end"]
        params |= {"start": span[0].isoformat(), "end": span[1].isoformat()}
    rows = await session.execute(
        text(
            f"SELECT f.message_id, {snippet} AS snip, m.role, m.created_at "
            "FROM messages_fts f JOIN messages m ON m.id = f.message_id "
            f"WHERE {' AND '.join(conditions)} ORDER BY {order} LIMIT :n"
        ),
        params,
    )
    return [
        (str(mid), str(snip), str(role), datetime.fromisoformat(str(created)))
        for mid, snip, role, created in rows
    ]


async def add_tool_call(session: AsyncSession, record: ToolCallRecord) -> None:
    session.add(record)


async def get_feedback(
    session: AsyncSession, user_id: int, message_id: str
) -> MessageFeedback | None:
    return await session.scalar(
        select(MessageFeedback).where(
            MessageFeedback.user_id == user_id, MessageFeedback.message_id == message_id
        )
    )
