"""The migration upgrades the supplied database and downgrades cleanly."""

import shutil
import sqlite3
from pathlib import Path

from tests.support import FIXTURE, migrate


def tables(path: Path) -> set[str]:
    with sqlite3.connect(path) as db:
        return {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def columns(path: Path, table: str) -> set[str]:
    with sqlite3.connect(path) as db:
        return {row[1] for row in db.execute(f"PRAGMA table_info({table})")}


def test_upgrade_and_downgrade(tmp_path: Path) -> None:
    path = tmp_path / "capper.db"
    shutil.copyfile(FIXTURE, path)
    migrate(path)
    upgraded = tables(path)
    assert {
        "turns",
        "messages",
        "messages_fts",
        "model_messages",
        "summaries",
        "promotions",
    } <= upgraded
    assert "Conversation_History" not in upgraded
    assert "image_url" in columns(path, "Products")
    assert "time_zone" in columns(path, "Users")
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM Users").fetchone() == (34,)

    migrate(path, "base", down=True)
    downgraded = tables(path)
    assert "turns" not in downgraded and "Conversation_History" in downgraded
    assert "image_url" not in columns(path, "Products")
    assert "time_zone" not in columns(path, "Users")
    migrate(path)
    assert tables(path) == upgraded
