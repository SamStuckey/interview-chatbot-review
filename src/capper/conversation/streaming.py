"""NDJSON stream events and the transcript parts they're saved as.

One JSON object per line, each with a `type`. Text is Markdown; cards carry
database-built items. A turn ends with exactly one terminal event:
`turn.end` or `error`.
"""

import json
from typing import Any, Literal

from capper.agent.deps import Card

GENERIC_ERROR_MESSAGE = (
    "Something went wrong and Capper couldn't finish this reply. Please try again."
)

type Event = dict[str, Any]


def turn_start(turn_id: str, user_message_id: str) -> Event:
    return {"type": "turn.start", "turn_id": turn_id, "user_message_id": user_message_id}


def text_delta(text: str) -> Event:
    return {"type": "text.delta", "text": text}


def card_event(card: Card) -> Event:
    return {
        "type": "card",
        "card_type": card.card_type,
        "heading": card.heading,
        "items": card.items,
    }


def turn_end(status: Literal["complete", "stopped"], assistant_message_id: str | None) -> Event:
    return {"type": "turn.end", "status": status, "assistant_message_id": assistant_message_id}


def error_event() -> Event:
    """The one terminal error event: generic, never naming the provider."""
    return {"type": "error", "code": "generic", "message": GENERIC_ERROR_MESSAGE}


def encode(event: Event) -> bytes:
    return (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


class TranscriptParts:
    """The assistant's parts exactly as sent: consecutive text deltas join into one text part."""

    def __init__(self) -> None:
        self.parts: list[dict[str, Any]] = []

    def add_text(self, text: str) -> None:
        if self.parts and self.parts[-1]["type"] == "text":
            self.parts[-1]["text"] += text
        else:
            self.parts.append({"type": "text", "text": text})

    def add_card(self, card: Card) -> None:
        self.parts.append(
            {
                "type": "card",
                "card_type": card.card_type,
                "heading": card.heading,
                "items": card.items,
            }
        )


def part_events(parts: list[dict[str, Any]]) -> list[Event]:
    """Stored parts replayed as stream events."""
    events: list[Event] = []
    for part in parts:
        if part["type"] == "text":
            events.append(text_delta(part["text"]))
        else:
            events.append(
                {
                    "type": "card",
                    "card_type": part["card_type"],
                    "heading": part["heading"],
                    "items": part["items"],
                }
            )
    return events


def searchable_text(parts: list[dict[str, Any]]) -> str:
    """Only text parts are indexed for history search; cards aren't."""
    return "\n\n".join(part["text"] for part in parts if part["type"] == "text")
