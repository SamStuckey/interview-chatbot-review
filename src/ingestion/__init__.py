"""Ingestion: the manifest's canonical source documents become content rows.

The manifest is an allowlist: files it doesn't list are never read.
MVP sources are Markdown curated by hand from the supplied PDFs, so no
PDF parser is used.
"""

from ingestion.manifest import ManifestEntry, load_manifest, normalize, read_sources
from ingestion.run import ingest

__all__ = ["ManifestEntry", "ingest", "load_manifest", "normalize", "read_sources"]
