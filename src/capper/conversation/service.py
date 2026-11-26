"""Conversation use cases: send and replay, history, stop, feedback, and saving a turn's end.

Transactions are short and happen at defined points: turn start, each tool
call's audit row, turn end.
"""

import hashlib
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from capper.conversation import repository
from capper.conversation.models import (
    TURN_COMPLETE,
    TURN_ERROR,
    TURN_IN_PROGRESS,
    TURN_STOPPED,
    Message,
    MessageFeedback,
    Summary,
    Turn,
)
from capper.conversation.streaming import (
    Event,
    error_event,
    part_events,
    searchable_text,
    turn_end,
    turn_start,
)
from capper.db import SessionFactory
from capper.errors import IdempotencyKeyReused, InvalidRequest, NotFound, TurnInProgress
from capper.paging import clamp_limit, decode_cursor, next_page
from capper.time import Clock
from content_bundle import ContentSet, read_active

HISTORY_PAGE_DEFAULT = 20
HISTORY_PAGE_MAX = 100
COMMENT_MAX_CHARS = 500

type EndStatus = Literal["complete", "stopped", "error"]


def request_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def greeting_bubbles(snapshot: ContentSet) -> list[str]:
    """The greeting document's paragraphs, one bubble each. Never stored in history."""
    document = snapshot.get("greeting")
    if document is None:
        return []
    return [block.strip() for block in document.body.split("\n\n") if block.strip()]


@dataclass(frozen=True)
class StartedTurn:
    turn_id: str
    user_id: int
    user_message_id: str
    text: str


@dataclass(frozen=True)
class Replay:
    events: list[Event]


@dataclass(frozen=True)
class ConversationState:
    greeting: list[str]
    turn_in_progress: bool
    active_turn_id: str | None


@dataclass(frozen=True)
class TranscriptMessage:
    id: str
    role: str
    created_at: datetime
    status: str
    parts: list[dict[str, Any]]


@dataclass(frozen=True)
class TranscriptPage:
    messages: list[TranscriptMessage]
    next_cursor: str | None


@dataclass(frozen=True)
class StoredHistory:
    """The latest summary and the model messages after its watermark, as stored (serialized)."""

    summary_id: int | None
    summary_payload: str | None
    payloads: list[str]
    row_ids: list[int | None]
    """Row ID per loaded message, the summary first as `None` (it isn't a stored row)."""
    watermark: int | None


@dataclass(frozen=True)
class SavedFeedback:
    message_id: str
    rating: str
    comment: str | None
    updated_at: datetime


@dataclass(frozen=True)
class NewSummary:
    """A compaction made during the run, serialized."""

    text: str
    payload: str
    first_kept: int
    """Index into `stored history + new messages` of the first message kept verbatim."""


@dataclass(frozen=True)
class SavedTurn:
    assistant_message_id: str | None
    """Set only if the turn produced parts."""
    summary_id: int | None
    """Set only if the turn compacted its history."""


@dataclass(frozen=True)
class TurnEnd:
    status: EndStatus
    parts: list[dict[str, Any]]
    new_payloads: list[str]
    summary: NewSummary | None
    summary_model: str
    content_version: str


class ConversationService:
    def __init__(
        self,
        sessions: SessionFactory,
        clock: Clock,
        *,
        max_message_chars: int,
        model_name: str,
        app_version: str,
        prompt_payload: Callable[[str], str],
    ) -> None:
        self._sessions = sessions
        self._prompt_payload = prompt_payload
        self._clock = clock
        self._max_message_chars = max_message_chars
        self._model_name = model_name
        self._app_version = app_version

    async def snapshot(self) -> ContentSet:
        """The active content set, read once per request or turn."""
        async with self._sessions() as session:
            return await read_active(session)

    async def state(self, user_id: int, snapshot: ContentSet) -> ConversationState:
        async with self._sessions() as session:
            active = await repository.active_turn(session, user_id)
        return ConversationState(
            greeting_bubbles(snapshot), active is not None, active.id if active else None
        )

    async def start_turn(
        self, user_id: int, text: str, idempotency_key: str, snapshot: ContentSet
    ) -> StartedTurn | Replay:
        """Validate, apply the duplicate-send rules, commit the turn before generation."""
        if not text.strip():
            raise InvalidRequest("text: the message is empty")
        if len(text) > self._max_message_chars:
            raise InvalidRequest(
                f"text: the message is longer than {self._max_message_chars} characters"
            )
        key = idempotency_key.strip()
        if not key or len(key) > 200:
            raise InvalidRequest("Idempotency-Key header: required, up to 200 characters")
        digest = request_hash(text)
        async with self._sessions() as session:
            existing = await repository.find_turn_by_key(session, user_id, key)
            if existing is not None:
                return await self._duplicate(session, user_id, existing, digest)
            active = await repository.active_turn(session, user_id)
            if active is not None:
                raise TurnInProgress("another reply is in progress", turn_id=active.id)

        now = self._clock()
        turn_id = uuid.uuid4().hex
        message_id = uuid.uuid4().hex
        parts = [{"type": "text", "text": text}]
        try:
            async with self._sessions() as session, session.begin():
                session.add(
                    Turn(
                        id=turn_id,
                        user_id=user_id,
                        status=TURN_IN_PROGRESS,
                        idempotency_key=key,
                        request_text_hash=digest,
                        model=self._model_name,
                        content_version=snapshot.version,
                        app_version=self._app_version,
                        started_at=now,
                        ended_at=None,
                    )
                )
                await session.flush()
                message = Message(
                    id=message_id,
                    user_id=user_id,
                    turn_id=turn_id,
                    role="user",
                    parts=parts,
                    created_at=now,
                )
                await repository.add_message(session, message, text)
                await repository.add_model_messages(
                    session, user_id, turn_id, [self._prompt_payload(text)], now
                )
        except IntegrityError:
            # A concurrent send won the race for the key or the one-active-turn index.
            async with self._sessions() as session:
                existing = await repository.find_turn_by_key(session, user_id, key)
                if existing is not None:
                    return await self._duplicate(session, user_id, existing, digest)
                active = await repository.active_turn(session, user_id)
            raise TurnInProgress(
                "another reply is in progress", turn_id=active.id if active else None
            ) from None
        return StartedTurn(turn_id, user_id, message_id, text)

    async def _duplicate(
        self, session: AsyncSession, user_id: int, turn: Turn, digest: str
    ) -> Replay:
        if turn.request_text_hash != digest:
            raise IdempotencyKeyReused(
                "this Idempotency-Key was already used with a different message"
            )
        if turn.status == TURN_IN_PROGRESS:
            raise TurnInProgress("this message is still being answered", turn_id=turn.id)
        return Replay(
            self._replay_events(turn, await repository.turn_messages(session, user_id, turn.id))
        )

    @staticmethod
    def _replay_events(turn: Turn, messages: list[Message]) -> list[Event]:
        """The stored turn as a short stream, ending as the original did."""
        user = next((m for m in messages if m.role == "user"), None)
        assistant = next((m for m in messages if m.role == "assistant"), None)
        events = [turn_start(turn.id, user.id if user else "")]
        if assistant is not None:
            events.extend(part_events(assistant.parts))
        if turn.status == TURN_ERROR:
            events.append(error_event())
        else:
            status: Literal["complete", "stopped"] = (
                "stopped" if turn.status == TURN_STOPPED else "complete"
            )
            events.append(turn_end(status, assistant.id if assistant else None))
        return events

    async def load_history(self, user_id: int) -> StoredHistory:
        """The latest summary plus every stored model message after its watermark."""
        async with self._sessions() as session:
            summary = await repository.latest_summary(session, user_id)
            watermark = summary.covers_through_model_message_id if summary else None
            rows = await repository.model_messages_after(session, user_id, watermark)
        row_ids: list[int | None] = ([None] if summary else []) + [r.id for r in rows]
        return StoredHistory(
            summary.id if summary else None,
            summary.payload if summary else None,
            [r.payload for r in rows],
            row_ids,
            watermark,
        )

    async def end_turn(
        self, started: StartedTurn, stored: StoredHistory, end: TurnEnd
    ) -> SavedTurn:
        """Save the turn's end in one transaction, before the terminal event."""
        now = self._clock()
        status = {"complete": TURN_COMPLETE, "stopped": TURN_STOPPED, "error": TURN_ERROR}[
            end.status
        ]
        assistant_id = uuid.uuid4().hex if end.parts else None
        summary_id: int | None = None
        async with self._sessions() as session, session.begin():
            new_ids = await repository.add_model_messages(
                session,
                started.user_id,
                started.turn_id,
                end.new_payloads,
                now,
            )
            if end.summary is not None:
                summary = Summary(
                    user_id=started.user_id,
                    covers_through_model_message_id=self._watermark(stored, new_ids, end.summary),
                    text=end.summary.text,
                    payload=end.summary.payload,
                    model=end.summary_model,
                    content_version=end.content_version,
                    created_at=now,
                )
                session.add(summary)
                await session.flush()
                summary_id = summary.id
            if assistant_id is not None:
                message = Message(
                    id=assistant_id,
                    user_id=started.user_id,
                    turn_id=started.turn_id,
                    role="assistant",
                    parts=end.parts,
                    created_at=now,
                )
                await repository.add_message(session, message, searchable_text(end.parts))
            turn = await repository.get_turn(session, started.user_id, started.turn_id)
            if turn is not None:
                turn.status = status
                turn.ended_at = now
        return SavedTurn(assistant_id, summary_id)

    @staticmethod
    def _watermark(stored: StoredHistory, new_ids: list[int], summary: NewSummary) -> int:
        """The row of the last message the summary replaced: just before the kept suffix."""
        ids: list[int | None] = [*stored.row_ids, *new_ids]
        replaced = ids[summary.first_kept - 1]
        if replaced is None:
            # Only the previous summary precedes the suffix: the new one keeps its watermark.
            if stored.watermark is None:
                raise RuntimeError("a summary without a watermark")
            return stored.watermark
        return replaced

    async def mark_error(self, started: StartedTurn) -> None:
        """The last resort when saving a turn's end failed: release the turn as `error`."""
        async with self._sessions() as session, session.begin():
            turn = await repository.get_turn(session, started.user_id, started.turn_id)
            if turn is not None and turn.status == TURN_IN_PROGRESS:
                turn.status = TURN_ERROR
                turn.ended_at = self._clock()

    async def recover_stale_turns(self) -> int:
        async with self._sessions() as session, session.begin():
            return await repository.mark_in_progress_as_error(session, self._clock())

    async def history(self, user_id: int, before: str | None, limit: int | None) -> TranscriptPage:
        size = clamp_limit(limit, default=HISTORY_PAGE_DEFAULT, maximum=HISTORY_PAGE_MAX)
        after = decode_cursor(before, (datetime, str))
        async with self._sessions() as session:
            rows = await repository.list_messages(session, user_id, after, size + 1)
        rows, cursor = next_page(rows, size, lambda row: (row[0].created_at, row[0].id))
        items = [
            TranscriptMessage(m.id, m.role, m.created_at, status, m.parts) for m, status in rows
        ]
        return TranscriptPage(items, cursor)

    async def turn_exists(self, user_id: int, turn_id: str) -> bool:
        async with self._sessions() as session:
            return await repository.get_turn(session, user_id, turn_id) is not None

    async def feedback(
        self, user_id: int, message_id: str, rating: Literal["up", "down"], comment: str | None
    ) -> SavedFeedback:
        """Create or replace the user's rating of one of their assistant messages."""
        if comment is not None and len(comment) > COMMENT_MAX_CHARS:
            raise InvalidRequest(f"comment: longer than {COMMENT_MAX_CHARS} characters")
        now = self._clock()
        async with self._sessions() as session, session.begin():
            message = await repository.get_message(session, user_id, message_id)
            if message is None or message.role != "assistant":
                raise NotFound("message not found")
            feedback = await repository.get_feedback(session, user_id, message_id)
            if feedback is None:
                feedback = MessageFeedback(
                    user_id=user_id,
                    message_id=message_id,
                    rating=rating,
                    comment=comment,
                    created_at=now,
                    updated_at=now,
                )
                session.add(feedback)
            else:
                feedback.rating = rating
                feedback.comment = comment
                feedback.updated_at = now
        return SavedFeedback(message_id, rating, comment, now)
