"""Running a turn in the background and streaming it.

The response streams from a queue that a lifespan-owned task fills. A client
disconnect doesn't cancel the task: the turn finishes and is saved.
Stop cancels the run through its token. Every ending is saved in
one transaction before its terminal event is sent.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from opentelemetry.trace import Span, Status, StatusCode, Tracer
from pydantic_ai import (
    CancellationToken,
    RunCancelled,
    RunTimedOut,
    UsageLimits,
    capture_run_messages,
)
from pydantic_ai.agent import EventStreamHandler
from pydantic_ai.exceptions import ModelAPIError
from pydantic_ai.messages import ModelMessage, ModelRequest
from pydantic_ai.usage import RunUsage

from capper.accounts.service import AccountService
from capper.agent.agent import CapperAgent, opaque_user_key, run_model_settings
from capper.agent.deps import CapperDeps, ToolBudget, ToolServices
from capper.context.builder import (
    account_context_request,
    account_view,
    dump_message,
    load_history,
    turn_context_request,
)
from capper.context.compaction import CompactionShapeError, find_compaction
from capper.context.inject import RequestContext
from capper.conversation.service import (
    ConversationService,
    EndStatus,
    NewSummary,
    StartedTurn,
    StoredHistory,
    TurnEnd,
)
from capper.conversation.stop import StopRegistry
from capper.conversation.streaming import error_event, turn_end, turn_start
from capper.conversation.turn_stream import EventQueue, TurnStream
from capper.conversation.turn_telemetry import (
    clearing_ran,
    failure_attributes,
    record_compaction,
    record_loaded_summary,
    record_outcome,
    record_saved_summary,
    record_unplaced_compaction,
)
from capper.memory.service import MemoryService
from capper.time import Clock, user_zone
from content_bundle import ContentSet

logger = logging.getLogger(__name__)


def messages_after(messages: list[ModelMessage], prompt: ModelMessage) -> list[ModelMessage]:
    """The run's own messages: everything after this turn's prompt, found by identity."""
    for index, message in enumerate(messages):
        if message is prompt:
            return messages[index + 1 :]
    return []


@dataclass(frozen=True)
class RunnerConfig:
    cache_key_secret: str
    default_timezone: str
    turn_timeout_seconds: float
    max_tool_calls_per_turn: int
    tool_result_max_chars: int
    compaction_model: str
    model_prices: dict[str, tuple[float, float, float]]


@dataclass
class RunOutcome:
    status: EndStatus
    new_messages: list[ModelMessage]
    final: list[ModelMessage]
    usage: RunUsage | None
    failure: dict[str, Any] = field(default_factory=dict[str, Any])
    """Content-free attributes saying why the run failed (`failure_attributes`)."""


class TurnRunner:
    def __init__(
        self,
        *,
        capper: CapperAgent,
        conversations: ConversationService,
        accounts: AccountService,
        memory: MemoryService,
        tool_services: ToolServices,
        stops: StopRegistry,
        tracer: Tracer,
        clock: Clock,
        config: RunnerConfig,
    ) -> None:
        self._capper = capper
        self._conversations = conversations
        self._accounts = accounts
        self._memory = memory
        self._tools = tool_services
        self._stops = stops
        self._tracer = tracer
        self._clock = clock
        self._config = config
        self._tasks: set[asyncio.Task[None]] = set()

    def start(self, started: StartedTurn, snapshot: ContentSet) -> EventQueue:
        """Start the turn's background task; the caller streams the returned queue."""
        queue: EventQueue = asyncio.Queue()
        queue.put_nowait(turn_start(started.turn_id, started.user_message_id))
        token = self._stops.register(started.turn_id)
        task = asyncio.create_task(
            self._run(started, snapshot, queue, token), name=f"turn-{started.turn_id}"
        )
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return queue

    async def shutdown(self) -> None:
        """Wait for running turns up to the turn timeout, then cancel the rest."""
        if self._tasks:
            _, pending = await asyncio.wait(self._tasks, timeout=self._config.turn_timeout_seconds)
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

    async def _run(
        self,
        started: StartedTurn,
        snapshot: ContentSet,
        queue: EventQueue,
        token: CancellationToken,
    ) -> None:
        with self._tracer.start_as_current_span("capper.turn") as span:
            key = opaque_user_key(self._config.cache_key_secret, started.user_id)
            span.set_attributes(
                {
                    "capper.user_key": key,
                    "capper.turn_id": started.turn_id,
                    "capper.model": self._capper.model_name,
                    "capper.content_version": snapshot.version,
                }
            )
            try:
                await self._execute(started, snapshot, queue, token, key, span)
            except asyncio.CancelledError:
                span.set_attribute("capper.status", "error")
                await self._fail(started, queue)
                raise
            except Exception:
                logger.exception("turn %s failed outside the run", started.turn_id)
                span.set_status(Status(StatusCode.ERROR))
                span.set_attribute("capper.status", "error")
                await self._fail(started, queue)
            finally:
                self._stops.release(started.turn_id)
                queue.put_nowait(None)

    async def _fail(self, started: StartedTurn, queue: EventQueue) -> None:
        try:
            await self._conversations.mark_error(started)
        finally:
            queue.put_nowait(error_event())

    async def _execute(
        self,
        started: StartedTurn,
        snapshot: ContentSet,
        queue: EventQueue,
        token: CancellationToken,
        key: str,
        span: Span,
    ) -> None:
        # Time to first token counts from here, so it includes loading the turn's context.
        began = time.perf_counter()
        profile, notes, stored = await asyncio.gather(
            self._accounts.profile(started.user_id),
            self._memory.active_notes(started.user_id),
            self._conversations.load_history(started.user_id),
        )
        if profile is None:
            raise RuntimeError("the turn's user no longer exists")
        record_loaded_summary(span, stored.summary_id)

        zone = user_zone(profile.time_zone, self._config.default_timezone)
        stream = TurnStream(queue, span, began)
        budget = ToolBudget(self._config.max_tool_calls_per_turn)
        deps = CapperDeps(
            user_id=started.user_id,
            turn_id=started.turn_id,
            snapshot=snapshot,
            profile=profile,
            time_zone=zone,
            services=self._tools,
            emit_card=stream.card,
            tool_budget=budget,
            tool_result_max_chars=self._config.tool_result_max_chars,
        )
        history = load_history(stored.summary_payload, stored.payloads)
        prompt = history[-1]
        assert isinstance(prompt, ModelRequest), "the stored history ends with this turn's prompt"
        request_context = RequestContext(
            account=account_context_request(
                account_view(profile.name, profile.school_name, notes, zone)
            ),
            turn=turn_context_request(self._clock().astimezone(zone)),
            prompt=prompt,
        )

        outcome = await self._run_agent(
            deps, history, prompt, request_context, token, key, stream.on_events
        )
        summary = self._compaction(history, stored, outcome, span)
        end = TurnEnd(
            status=outcome.status,
            parts=stream.transcript.parts,
            new_payloads=[dump_message(message) for message in outcome.new_messages],
            summary=summary,
            summary_model=self._config.compaction_model,
            content_version=snapshot.version,
        )
        try:
            saved = await self._conversations.end_turn(started, stored, end)
        except Exception:
            logger.exception("saving turn %s failed", started.turn_id)
            span.set_attribute("capper.status", "error")
            await self._fail(started, queue)
            return
        record_saved_summary(span, saved.summary_id)
        record_outcome(
            span,
            status=outcome.status,
            failure=outcome.failure,
            usage=outcome.usage,
            tool_calls=budget.used,
            compacted=summary is not None,
            cleared=clearing_ran(outcome.final),
            first_token_ms=stream.first_token_ms,
            prices=self._config.model_prices.get(self._capper.model_name),
        )
        if outcome.status == "error":
            await queue.put(error_event())
        else:
            await queue.put(turn_end(outcome.status, saved.assistant_message_id))

    async def _run_agent(
        self,
        deps: CapperDeps,
        history: list[ModelMessage],
        prompt: ModelRequest,
        request_context: RequestContext,
        token: CancellationToken,
        key: str,
        on_events: EventStreamHandler[CapperDeps],
    ) -> RunOutcome:
        with capture_run_messages() as captured:
            try:
                result = await self._capper.agent.run(
                    None,
                    message_history=history,
                    deps=deps,
                    conversation_id=key,
                    model_settings=run_model_settings(key),
                    usage_limits=UsageLimits(request_limit=self._capper.request_limit),
                    cancellation_token=token,
                    timeout=self._config.turn_timeout_seconds,
                    event_stream_handler=on_events,
                    capabilities=[request_context],
                )
                return RunOutcome(
                    "complete", result.new_messages(), result.all_messages(), result.usage
                )
            except RunTimedOut as error:
                logger.warning("turn %s timed out", deps.turn_id)
                return RunOutcome(
                    "error",
                    error.new_messages(),
                    error.all_messages(),
                    error.usage,
                    {"error.type": "timeout"},
                )
            except RunCancelled as error:
                return RunOutcome(
                    "stopped", error.new_messages(), error.all_messages(), error.usage
                )
            except Exception as error:
                failure = failure_attributes(error)
                if isinstance(error, ModelAPIError):
                    # The provider's message can echo the request, so only its category is logged.
                    logger.error("turn %s failed: %s", deps.turn_id, failure)
                else:
                    logger.exception("turn %s failed", deps.turn_id)
                final = list(captured)
                return RunOutcome("error", messages_after(final, prompt), final, None, failure)

    def _compaction(
        self, history: list[ModelMessage], stored: StoredHistory, outcome: RunOutcome, span: Span
    ) -> NewSummary | None:
        try:
            compaction = find_compaction(history, outcome.new_messages, outcome.final)
        except CompactionShapeError:
            # Never guess a watermark: without a summary row, the next turn reloads everything.
            logger.exception("compaction result has an unexpected shape; summary not saved")
            record_unplaced_compaction(span)
            return None
        if compaction is None:
            return None
        record_compaction(span, previous_cutoff=stored.watermark, kept_from=compaction.first_kept)
        return NewSummary(compaction.text, dump_message(compaction.summary), compaction.first_kept)
