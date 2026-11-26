"""The health endpoint answers without a token."""

from pathlib import Path

from tests.support import Keys, ScriptedModel, running_app


async def test_healthz_reports_ok_when_the_database_answers(db_path: Path, keys: Keys) -> None:
    async with running_app(db_path, keys, ScriptedModel()) as h:
        response = await h.client.get("/healthz")
    assert response.status_code == 200 and response.json() == {"status": "ok"}
