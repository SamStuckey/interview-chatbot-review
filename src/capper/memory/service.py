"""Saved-guidance and avoid-list use cases.

Writes save immediately and return what changed so the agent can disclose it.
Caps return an explicit "full" result rather than silently dropping a write.
The avoid list is managed by product name: a name that matches more than one
product changes nothing and lists the candidates instead.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from capper.db import SessionFactory
from capper.errors import InvalidRequest, LimitReached, NotFound
from capper.memory import repository
from capper.memory.models import AvoidedProduct, GuidanceNote
from capper.time import Clock


@dataclass(frozen=True)
class SavedNote:
    note_id: int
    text: str
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class NamedProduct:
    product_id: int
    name: str


MAX_CANDIDATES = 5


def _saved(note: GuidanceNote) -> SavedNote:
    return SavedNote(note.id, note.text, note.expires_at, note.created_at, note.updated_at)


def _normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def matching_names(text: str, items: Sequence[NamedProduct]) -> list[NamedProduct]:
    """Items named exactly `text` if any, else items whose name contains it (any case)."""
    wanted = _normalized(text)
    if not wanted:
        raise InvalidRequest("give the product's name")
    exact = [item for item in items if _normalized(item.name) == wanted]
    return exact or [item for item in items if wanted in _normalized(item.name)]


def single_match(text: str, matches: list[NamedProduct], where: str) -> NamedProduct:
    """The single match, or an error the model can act on: none, or which ones to ask about."""
    if not matches:
        raise NotFound(f"nothing {where} matches {text!r}")
    if len(matches) > 1:
        names = "; ".join(f"{m.name} (product_id {m.product_id})" for m in matches)
        raise InvalidRequest(
            f"more than one product {where} matches {text!r}: {names}. Nothing was changed; "
            "ask the user which one they mean."
        )
    return matches[0]


class MemoryService:
    def __init__(
        self,
        sessions: SessionFactory,
        clock: Clock,
        *,
        max_notes: int,
        max_chars: int,
        max_avoided: int,
    ) -> None:
        self._sessions = sessions
        self._clock = clock
        self._max_notes = max_notes
        self._max_chars = max_chars
        self._max_avoided = max_avoided

    def _check_text(self, text: str) -> str:
        text = " ".join(text.split())
        if not text:
            raise InvalidRequest("the note is empty")
        if len(text) > self._max_chars:
            raise InvalidRequest(
                f"the note is longer than {self._max_chars} characters; shorten it"
            )
        return text

    def _check_expiry(self, expires_at: datetime | None) -> None:
        if expires_at is not None and expires_at <= self._clock():
            raise InvalidRequest("the expiry date is in the past")

    async def active_notes(self, user_id: int) -> list[SavedNote]:
        """Unexpired notes, oldest first, for the account context."""
        async with self._sessions() as session:
            notes = await repository.list_notes(session, user_id, self._clock())
        return [_saved(n) for n in notes]

    async def avoided(self, user_id: int) -> list[NamedProduct]:
        """The avoid list with product names, oldest first."""
        async with self._sessions() as session:
            rows = await repository.list_avoided(session, user_id)
        return [NamedProduct(product_id, name) for product_id, name in rows]

    async def add_note(self, user_id: int, text: str, expires_at: datetime | None) -> SavedNote:
        text = self._check_text(text)
        self._check_expiry(expires_at)
        now = self._clock()
        async with self._sessions() as session, session.begin():
            if await repository.count_notes(session, user_id) >= self._max_notes:
                raise LimitReached(
                    f"guidance full: {self._max_notes} notes saved; remove or update one first"
                )
            note = GuidanceNote(
                user_id=user_id, text=text, expires_at=expires_at, created_at=now, updated_at=now
            )
            session.add(note)
            await session.flush()
            return _saved(note)

    async def update_note(
        self, user_id: int, note_id: int, text: str, expires_at: datetime | None
    ) -> SavedNote:
        text = self._check_text(text)
        self._check_expiry(expires_at)
        async with self._sessions() as session, session.begin():
            note = await repository.get_note(session, user_id, note_id)
            if note is None:
                raise NotFound(f"note {note_id} not found")
            note.text = text
            note.expires_at = expires_at
            note.updated_at = self._clock()
            return _saved(note)

    async def remove_note(self, user_id: int, note_id: int) -> None:
        async with self._sessions() as session, session.begin():
            if not await repository.delete_note(session, user_id, note_id):
                raise NotFound(f"note {note_id} not found")

    async def avoid(self, user_id: int, product_name: str) -> NamedProduct:
        """Avoid the one catalog product `product_name` names (an exact name wins)."""
        async with self._sessions() as session, session.begin():
            candidates = await repository.products_named(
                session, _normalized(product_name), MAX_CANDIDATES
            )
            item = single_match(
                product_name,
                matching_names(product_name, [NamedProduct(p, n) for p, n in candidates]),
                "in the catalog",
            )
            product_id = item.product_id
            if await session.get(AvoidedProduct, (user_id, product_id)) is not None:
                return item
            if await repository.count_avoided(session, user_id) >= self._max_avoided:
                raise LimitReached(
                    f"list full: {self._max_avoided} products avoided; remove one first"
                )
            session.add(
                AvoidedProduct(user_id=user_id, product_id=product_id, created_at=self._clock())
            )
            return item

    async def unavoid(
        self, user_id: int, *, product_name: str | None = None, product_id: int | None = None
    ) -> NamedProduct:
        """Remove one product from the avoid list, by name (matched within it) or by ID."""
        if (product_name is None) == (product_id is None):
            raise InvalidRequest("give exactly one of product_name or product_id")
        avoided = await self.avoided(user_id)
        if product_name is not None:
            item = single_match(
                product_name, matching_names(product_name, avoided), "on the avoid list"
            )
        else:
            item = next((a for a in avoided if a.product_id == product_id), None)
            if item is None:
                raise NotFound(f"product {product_id} is not on the avoid list")
        async with self._sessions() as session, session.begin():
            await repository.delete_avoided(session, user_id, item.product_id)
        return item
