"""API routes require a token; demo sign-in routes do not."""

from pathlib import Path

from tests.support import ESTABLISHED_USER, Keys, ScriptedModel, running_app


async def test_api_routes_need_a_token_and_demo_routes_do_not(db_path: Path, keys: Keys) -> None:
    async with running_app(db_path, keys, ScriptedModel()) as h:
        for method, path in [
            ("GET", "/v1/conversation"),
            ("GET", "/v1/conversation/messages"),
            ("POST", "/v1/conversation/messages"),
            ("POST", "/v1/conversation/turns/abc/stop"),
            ("POST", "/v1/conversation/messages/abc/feedback"),
        ]:
            response = await h.client.request(method, path, json={})
            assert response.status_code == 401, path
            assert response.json()["error"]["code"] == "not_authenticated"

        users = await h.client.get("/demo/users")
        assert users.status_code == 200
        assert any(user["id"] == ESTABLISHED_USER for user in users.json())

        session = await h.client.post("/demo/sessions", json={"user_id": ESTABLISHED_USER})
        assert session.status_code == 200
        headers = {"Authorization": f"Bearer {session.json()['access_token']}"}
        assert (await h.client.get("/v1/conversation", headers=headers)).status_code == 200

        missing = await h.client.post("/demo/sessions", json={"user_id": 999_999})
        assert missing.status_code == 404
        assert (await h.client.get("/")).status_code == 200
