"""Reading the manifest and the Markdown sources it lists."""

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from content_bundle import DocumentSource
from content_bundle.store import CONTENT_CLASSES, LOAD_MODES


@dataclass(frozen=True)
class ManifestEntry:
    name: str
    content_class: str
    load: str
    file: str


def load_manifest(manifest_path: Path) -> list[ManifestEntry]:
    """Parse `[[documents]]` entries; reject unknown classes, load modes and duplicate names."""
    data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    entries = [
        ManifestEntry(
            name=str(item["name"]),
            content_class=str(item["class"]),
            load=str(item["load"]),
            file=str(item["file"]),
        )
        for item in data.get("documents", [])
    ]
    seen: set[str] = set()
    for entry in entries:
        if entry.name in seen:
            raise ValueError(f"duplicate document name in manifest: {entry.name}")
        seen.add(entry.name)
        if entry.content_class not in CONTENT_CLASSES:
            raise ValueError(f"{entry.name}: unknown class {entry.content_class!r}")
        if entry.load not in LOAD_MODES:
            raise ValueError(f"{entry.name}: unknown load {entry.load!r}")
    return entries


_AUTHOR_NOTE = re.compile(r"<!--.*?-->", re.DOTALL)


def normalize(body: str) -> str:
    """Drop authoring notes (HTML comments, which are for people, never the model) and normalize
    whitespace so cosmetic edits don't change the hash."""
    body = _AUTHOR_NOTE.sub("", body)
    lines = [line.rstrip() for line in body.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    text = "\n".join(lines).strip("\n")
    return re.sub(r"\n{3,}", "\n\n", text) + "\n"


def read_sources(manifest_path: Path) -> list[DocumentSource]:
    """Load every manifest entry's file, relative to the manifest's directory."""
    base = manifest_path.parent
    sources: list[DocumentSource] = []
    for entry in load_manifest(manifest_path):
        body = normalize((base / entry.file).read_text(encoding="utf-8"))
        sources.append(
            DocumentSource(
                name=entry.name,
                content_class=entry.content_class,  # pyright: ignore[reportArgumentType]
                load=entry.load,  # pyright: ignore[reportArgumentType]
                body=body,
            )
        )
    return sources
