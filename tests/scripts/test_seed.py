"""Seeding is idempotent and gives demo users their account data and preferences."""

import sqlite3
from pathlib import Path

from capper.catalog.images import PRODUCT_IMAGES, product_image_url
from tests.support import ESTABLISHED_USER, GUIDANCE_USER, seed_and_ingest


def counts(path: Path) -> tuple[int, ...]:
    with sqlite3.connect(path) as db:
        return tuple(
            db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in (
                "Products",
                "promotions",
                "referral_codes",
                "Purchase_History",
                "guidance_notes",
                "avoided_products",
                "Users",
            )
        )


async def test_seeding_twice_changes_nothing(db_path: Path) -> None:
    before = counts(db_path)
    await seed_and_ingest(db_path)
    assert counts(db_path) == before


def test_seed_users_have_their_roles(db_path: Path) -> None:
    with sqlite3.connect(db_path) as db:
        new_user = db.execute(
            "SELECT id, school_id FROM Users WHERE email = 'new.user@example.com'"
        ).fetchone()
        assert new_user is not None and new_user[1] is None
        for table in ("Purchase_History", "referral_codes", "guidance_notes"):
            count = db.execute(f"SELECT count(*) FROM {table} WHERE user_id = ?", (new_user[0],))
            assert count.fetchone() == (0,), table
        assert db.execute(
            "SELECT count(*) FROM referral_codes WHERE user_id = ?", (ESTABLISHED_USER,)
        ).fetchone() == (1,)
        notes = [
            r[0]
            for r in db.execute(
                "SELECT text FROM guidance_notes WHERE user_id = ?", (GUIDANCE_USER,)
            )
        ]
        assert "Allergic to peanuts." in notes
        assert db.execute("SELECT count(*) FROM Products WHERE image_url IS NULL").fetchone() == (
            0,
        )
        assert db.execute("SELECT count(*) FROM Users WHERE time_zone IS NULL").fetchone() == (0,)


def test_every_product_image_ships_with_the_app(db_path: Path) -> None:
    """Images are assets in the package and image, never external URLs."""
    with sqlite3.connect(db_path) as db:
        rows = db.execute("SELECT name, image_url FROM Products").fetchall()
    for name, url in rows:
        assert url == product_image_url(name)
        assert (PRODUCT_IMAGES / Path(url).name).is_file(), name
