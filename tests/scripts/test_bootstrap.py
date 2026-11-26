"""Bootstrap initializes an empty installation and leaves an initialized one unchanged."""

import sqlite3
from pathlib import Path

import pytest

from scripts import bootstrap


def test_bootstrap_from_nothing_then_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    database = tmp_path / "data" / "capper.db"
    monkeypatch.setenv("CAPPER_DATABASE_URL", f"sqlite+aiosqlite:///{database}")
    monkeypatch.setenv("CAPPER_JWT_PRIVATE_KEY_PATH", str(tmp_path / "data/keys/private.pem"))
    monkeypatch.setenv("CAPPER_JWT_PUBLIC_KEY_PATH", str(tmp_path / "data/keys/public.pem"))

    assert bootstrap.main() == 0
    first = capsys.readouterr().out
    assert "keys: created" in first and "copied from the supplied fixture" in first
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT count(*) FROM content_documents WHERE active").fetchone()[0] > 0
        products = db.execute("SELECT count(*) FROM Products").fetchone()

    assert bootstrap.main() == 0
    second = capsys.readouterr().out
    assert "keys: present" in second and "database: present" in second
    assert "no changes" in second
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT count(*) FROM Products").fetchone() == products
