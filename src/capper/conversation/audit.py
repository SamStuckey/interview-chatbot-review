"""The tool-call audit log."""

from typing import Any

from capper.conversation import repository
from capper.conversation.models import ToolCallRecord
from capper.db import SessionFactory
from capper.time import Clock


class ToolAuditLog:
    """Each tool call's audit row, in its own short transaction."""

    def __init__(self, sessions: SessionFactory, clock: Clock) -> None:
        self._sessions = sessions
        self._clock = clock

    async def record(
        self,
        *,
        user_id: int,
        turn_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        status: str,
        latency_ms: int,
    ) -> None:
        async with self._sessions() as session, session.begin():
            await repository.add_tool_call(
                session,
                ToolCallRecord(
                    user_id=user_id,
                    turn_id=turn_id,
                    tool_name=tool_name,
                    arguments=arguments,
                    status=status,
                    latency_ms=latency_ms,
                    created_at=self._clock(),
                ),
            )
