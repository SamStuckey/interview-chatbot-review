"""Request and response bodies for the conversation API. JSON is snake_case."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorDetail(BaseModel):
    code: str
    message: str
    turn_id: str | None = None


class ErrorOut(BaseModel):
    """Every error before streaming starts."""

    error: ErrorDetail


class ConversationOut(BaseModel):
    greeting: list[str]
    turn_in_progress: bool
    active_turn_id: str | None


class MessageOut(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    created_at: datetime
    status: str
    parts: list[dict[str, Any]]


class MessagesOut(BaseModel):
    messages: list[MessageOut]
    next_cursor: str | None


class SendIn(Strict):
    text: str


class StopOut(BaseModel):
    stopped: bool


class FeedbackIn(Strict):
    rating: Literal["up", "down"]
    comment: str | None = Field(default=None, max_length=500)


class FeedbackOut(BaseModel):
    message_id: str
    rating: Literal["up", "down"]
    comment: str | None
    updated_at: datetime
