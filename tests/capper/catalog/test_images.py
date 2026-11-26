"""Product images are assets served by the app, never external URLs."""

from pathlib import Path

from tests.support import Keys, ScriptedModel, running_app


async def test_product_images_are_served_by_the_app(db_path: Path, keys: Keys) -> None:
    async with running_app(db_path, keys, ScriptedModel()) as h:
        image = await h.client.get("/images/products/macaroni-cheese-box.svg")
        missing = await h.client.get("/images/products/nope.svg")
    assert image.status_code == 200 and image.headers["content-type"].startswith("image/svg")
    assert missing.status_code == 404
