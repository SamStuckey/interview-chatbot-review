"""`CapperDeps`: everything a turn's tools and capabilities need, built once per turn.

`user_id` here is the only identity tools ever see.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal, Protocol
from zoneinfo import ZoneInfo

from capper.accounts.service import AccountProfile, AccountService
from capper.catalog.service import CatalogService
from capper.memory.service import MemoryService
from content_bundle import ContentSet


@dataclass(frozen=True)
class Card:
    """A card event's payload, built from database records."""

    card_type: Literal["product", "promotion"]
    heading: str
    items: list[dict[str, Any]]


type CardSink = Callable[[Card], Awaitable[None]]


@dataclass(frozen=True)
class HistoryMatch:
    message_id: str
    created_at: datetime
    role: str
    snippet: str


class HistorySearch(Protocol):
    async def search(
        self,
        user_id: int,
        *,
        query: str | None,
        first_day: date | None,
        last_day: date | None,
        zone: ZoneInfo,
        limit: int,
    ) -> list[HistoryMatch]: ...


class ToolAudit(Protocol):
    async def record(
        self,
        *,
        user_id: int,
        turn_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        status: str,
        latency_ms: int,
    ) -> None: ...


@dataclass
class ToolBudget:
    """The per-turn tool-call limit. One per turn; counts calls as they start."""

    limit: int
    used: int = 0

    def take(self) -> bool:
        """Claim one call; `False` once the limit is reached."""
        if self.used >= self.limit:
            return False
        self.used += 1
        return True

    @property
    def exhausted(self) -> bool:
        return self.used >= self.limit


@dataclass(frozen=True)
class ToolServices:
    catalog: CatalogService
    memory: MemoryService
    accounts: AccountService
    history: HistorySearch
    audit: ToolAudit


@dataclass
class CapperDeps:
    user_id: int
    turn_id: str
    snapshot: ContentSet
    profile: AccountProfile
    time_zone: ZoneInfo
    """The user's own zone, or the configured default, for local dates and times."""
    services: ToolServices
    emit_card: CardSink
    tool_budget: ToolBudget
    tool_result_max_chars: int
