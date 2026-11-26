"""Publishing the manifest's documents through `content_bundle`."""

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from content_bundle import PublishResult, publish
from ingestion.manifest import read_sources


async def ingest(session: AsyncSession, manifest_path: Path) -> PublishResult:
    """Publish the manifest's sources as one set. Takes effect on the next turn."""
    return await publish(session, read_sources(manifest_path))
