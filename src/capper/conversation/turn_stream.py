"""What the client sees of a running turn: its events, the parts to save, and the first words.

Text and cards are queued for the response stream as they happen, and kept as
the transcript parts saved with the turn.
"""

import asyncio
import time
from collections.abc import AsyncIterable

from opentelemetry.trace import Span
from pydantic_ai import AgentStreamEvent, RunContext
from pydantic_ai.messages import PartDeltaEvent, PartStartEvent, TextPart, TextPartDelta
from pydantic_ai_harness.compaction import ContextUsageMeasuredEvent

from capper.agent.deps import CapperDeps, Card
from capper.conversation.streaming import Event, TranscriptParts, card_event, text_delta

type EventQueue = asyncio.Queue[Event | None]


class TurnStream:
    def __init__(self, queue: EventQueue, span: Span, began: float) -> None:
        self.transcript = TranscriptParts()
        self.first_token_ms: int | None = None
        """Elapsed time from turn start, including loading the turn's context."""
        self._queue = queue
        self._span = span
        self._began = began

    async def card(self, card: Card) -> None:
        """The tools' card sink (`CapperDeps.emit_card`)."""
        self.transcript.add_card(card)
        await self._queue.put(card_event(card))

    async def on_events(
        self, _ctx: RunContext[CapperDeps], events: AsyncIterable[AgentStreamEvent]
    ) -> None:
        """The agent's event handler: text goes to the client, context usage to the trace."""
        async for event in events:
            if isinstance(event, PartStartEvent) and isinstance(event.part, TextPart):
                await self._text(event.part.content)
            elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                await self._text(event.delta.content_delta)
            elif isinstance(event, ContextUsageMeasuredEvent):
                self._span.add_event(
                    "context.usage",
                    {"used_tokens": event.used_tokens, "budget_tokens": event.window_tokens},
                )

    async def _text(self, text: str) -> None:
        if not text:
            return
        if self.first_token_ms is None:
            self.first_token_ms = int((time.perf_counter() - self._began) * 1000)
        self.transcript.add_text(text)
        await self._queue.put(text_delta(text))
