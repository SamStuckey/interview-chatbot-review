"""Content documents: the table, the content version and publishing."""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, get_args

from sqlalchemy import Boolean, Index, Integer, String, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

type ContentClass = Literal["operator_policy", "user_knowledge"]
type LoadMode = Literal["always", "on_demand", "app"]

CONTENT_CLASSES: tuple[str, ...] = get_args(ContentClass.__value__)
LOAD_MODES: tuple[str, ...] = get_args(LoadMode.__value__)


class ContentBase(DeclarativeBase):
    """The content table's own base, so this package depends on neither `capper` nor `ingestion`."""


class ContentDocument(ContentBase):
    __tablename__ = "content_documents"
    __table_args__ = (
        Index(
            "uq_content_documents_active_name",
            "name",
            unique=True,
            sqlite_where=text("active = 1"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    content_class: Mapped[str] = mapped_column(String)
    load: Mapped[str] = mapped_column(String)
    body: Mapped[str] = mapped_column(String)
    content_hash: Mapped[str] = mapped_column(String)
    active: Mapped[bool] = mapped_column(Boolean)
    ingested_at: Mapped[str] = mapped_column(String)


@dataclass(frozen=True)
class DocumentSource:
    """One document as ingestion wants it published."""

    name: str
    content_class: ContentClass
    load: LoadMode
    body: str

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.body.encode()).hexdigest()


@dataclass(frozen=True)
class ActiveDocument:
    name: str
    content_class: str
    load: str
    body: str
    content_hash: str


@dataclass(frozen=True)
class ContentSet:
    """The active documents and their content version: one turn's snapshot."""

    documents: tuple[ActiveDocument, ...]
    version: str

    def get(self, name: str) -> ActiveDocument | None:
        return next((doc for doc in self.documents if doc.name == name), None)

    def with_load(self, load: LoadMode) -> tuple[ActiveDocument, ...]:
        return tuple(doc for doc in self.documents if doc.load == load)


@dataclass(frozen=True)
class PublishResult:
    published: tuple[str, ...]
    unchanged: tuple[str, ...]
    deactivated: tuple[str, ...]
    version: str


def content_version(documents: tuple[ActiveDocument, ...]) -> str:
    """SHA-256 over each active document's (name, class, load, hash), sorted by name."""
    rows = sorted((d.name, d.content_class, d.load, d.content_hash) for d in documents)
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()[:16]


async def read_active(session: AsyncSession) -> ContentSet:
    """Read the active set once; the caller holds it for the whole turn."""
    rows = (
        await session.scalars(
            select(ContentDocument).where(ContentDocument.active).order_by(ContentDocument.name)
        )
    ).all()
    documents = tuple(
        ActiveDocument(r.name, r.content_class, r.load, r.body, r.content_hash) for r in rows
    )
    return ContentSet(documents=documents, version=content_version(documents))


async def publish(session: AsyncSession, sources: list[DocumentSource]) -> PublishResult:
    """Publish a full set in one transaction.

    A document whose name, class, load and hash are unchanged is left alone. A
    changed one is inserted as a new active row and the old row's `active`
    flag is cleared, the only update ever made. A document missing from the
    set is deactivated. Published bodies are never edited. The caller's
    session is committed (or rolled back) here, whatever it read before.
    """
    names = [source.name for source in sources]
    if len(names) != len(set(names)):
        raise ValueError("document names must be unique")
    for source in sources:
        if source.content_class not in CONTENT_CLASSES or source.load not in LOAD_MODES:
            raise ValueError(f"{source.name}: unknown class or load")

    now = datetime.now(UTC).isoformat()
    try:
        current = {
            row.name: row
            for row in (
                await session.scalars(select(ContentDocument).where(ContentDocument.active))
            ).all()
        }
        published: list[str] = []
        unchanged: list[str] = []
        for source in sources:
            existing = current.get(source.name)
            key = (source.content_class, source.load, source.content_hash)
            if existing and (existing.content_class, existing.load, existing.content_hash) == key:
                unchanged.append(source.name)
                continue
            if existing:
                await session.execute(
                    update(ContentDocument)
                    .where(ContentDocument.id == existing.id)
                    .values(active=False)
                )
            session.add(
                ContentDocument(
                    name=source.name,
                    content_class=source.content_class,
                    load=source.load,
                    body=source.body,
                    content_hash=source.content_hash,
                    active=True,
                    ingested_at=now,
                )
            )
            published.append(source.name)
        deactivated = sorted(set(current) - set(names))
        if deactivated:
            await session.execute(
                update(ContentDocument)
                .where(ContentDocument.name.in_(deactivated), ContentDocument.active)
                .values(active=False)
            )
        await session.commit()
    except BaseException:
        await session.rollback()
        raise
    active = await read_active(session)
    return PublishResult(tuple(published), tuple(unchanged), tuple(deactivated), active.version)
