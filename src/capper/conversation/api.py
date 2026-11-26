"""Conversation routes. HTTP only: parsing, status codes and streaming.

Errors before streaming are HTTP statuses with the JSON error body; once the
200 stream has begun, a failure is one terminal `error` event.
"""

from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import StreamingResponse

from capper.auth.api import CurrentUser
from capper.container import Services
from capper.conversation.schemas import (
    ConversationOut,
    ErrorOut,
    FeedbackIn,
    FeedbackOut,
    MessageOut,
    MessagesOut,
    SendIn,
    StopOut,
)
from capper.conversation.service import Replay
from capper.conversation.streaming import Event, encode
from capper.errors import NotFound

ERRORS: dict[int | str, dict[str, Any]] = {
    status: {"model": ErrorOut, "description": description}
    for status, description in {
        401: "Missing, invalid or expired token, or an unknown user",
        404: "Not found, or not the caller's",
        409: "Another reply is in progress (`turn_in_progress`, with its `turn_id`)",
        422: "Invalid request, or `idempotency_key_reused`",
    }.items()
}

router = APIRouter(prefix="/v1/conversation", tags=["conversation"], responses=ERRORS)

NDJSON = "application/x-ndjson"


def _services(request: Request) -> Services:
    return request.app.state.services


@router.get("")
async def get_conversation(request: Request, user_id: CurrentUser) -> ConversationOut:
    """The greeting and whether a reply is running."""
    services = _services(request)
    state = await services.conversations.state(user_id, await services.conversations.snapshot())
    return ConversationOut(
        greeting=state.greeting,
        turn_in_progress=state.turn_in_progress,
        active_turn_id=state.active_turn_id,
    )


@router.get("/messages")
async def list_messages(
    request: Request,
    user_id: CurrentUser,
    before: Annotated[str | None, Query()] = None,
    limit: Annotated[int | None, Query(ge=1)] = None,
) -> MessagesOut:
    """The transcript, newest first."""
    page = await _services(request).conversations.history(user_id, before, limit)
    return MessagesOut(
        messages=[MessageOut.model_validate(m, from_attributes=True) for m in page.messages],
        next_cursor=page.next_cursor,
    )


async def _stream_list(events: list[Event]) -> AsyncIterator[bytes]:
    for event in events:
        yield encode(event)


@router.post(
    "/messages",
    response_class=StreamingResponse,
    responses={200: {"content": {NDJSON: {}}, "description": "An NDJSON stream of turn events"}},
)
async def send_message(
    request: Request,
    body: SendIn,
    user_id: CurrentUser,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> StreamingResponse:
    """Send a message and stream the reply, or replay a finished duplicate."""
    services = _services(request)
    snapshot = await services.conversations.snapshot()
    outcome = await services.conversations.start_turn(user_id, body.text, idempotency_key, snapshot)
    if isinstance(outcome, Replay):
        return StreamingResponse(_stream_list(outcome.events), media_type=NDJSON)
    queue = services.runner.start(outcome, snapshot)

    async def stream() -> AsyncIterator[bytes]:
        # Disconnecting stops this generator only; the turn's task keeps running.
        while (event := await queue.get()) is not None:
            yield encode(event)

    return StreamingResponse(stream(), media_type=NDJSON)


@router.post("/turns/{turn_id}/stop", status_code=202)
async def stop_turn(request: Request, turn_id: str, user_id: CurrentUser) -> StopOut:
    """Stop a running turn. Another user's turn is 404; an ended one has nothing to stop."""
    services = _services(request)
    if not await services.conversations.turn_exists(user_id, turn_id):
        raise NotFound("turn not found")
    return StopOut(stopped=services.stops.stop(turn_id))


@router.post("/messages/{message_id}/feedback")
async def give_feedback(
    request: Request, message_id: str, body: FeedbackIn, user_id: CurrentUser
) -> FeedbackOut:
    """Rate one of your assistant messages; a new rating replaces the old."""
    saved = await _services(request).conversations.feedback(
        user_id, message_id, body.rating, body.comment
    )
    return FeedbackOut(
        message_id=saved.message_id,
        rating=saved.rating,  # pyright: ignore[reportArgumentType]
        comment=saved.comment,
        updated_at=saved.updated_at,
    )
