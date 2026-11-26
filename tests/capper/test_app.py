"""The committed OpenAPI snapshot matches the app, so a contract change shows in the diff."""

import json
from pathlib import Path

from tests.support import Keys, ScriptedModel, running_app

SNAPSHOT = Path(__file__).with_name("openapi.json")


async def test_the_openapi_snapshot_is_current(db_path: Path, keys: Keys) -> None:
    async with running_app(db_path, keys, ScriptedModel()) as h:
        current = h.app.openapi()
    committed = json.loads(SNAPSHOT.read_text())
    assert committed == current, (
        "tests/capper/openapi.json is stale; regenerate it with "
        "`docker compose run --rm dev python -m scripts.export_openapi > tests/capper/openapi.json`"
    )
