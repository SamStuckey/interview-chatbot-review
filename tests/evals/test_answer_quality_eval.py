"""Answer-quality eval wiring, without any real model or judge calls."""

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import httpx
import pytest
from fastapi import FastAPI
from pydantic_evals import Case
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

from capper.app import create_app
from capper.config import Settings
from evals import answer_quality_eval
from evals.answer_quality_eval import Answer, answer
from evals.support import TurnInput, copy_database
from tests.support import Auxiliary, Keys, ScriptedModel, Step, make_settings


async def test_judge_receives_text_and_cards() -> None:
    card = {"type": "card", "card_type": "products", "heading": "Snacks", "items": [{"id": 7}]}
    events = [
        {"type": "turn.start", "turn_id": "t1"},
        {"type": "text.delta", "text": "Showing "},
        {"type": "text.delta", "text": "1 of 18."},
        card,
        {"type": "turn.end", "status": "complete"},
    ]

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/demo/sessions":
            assert json.loads(request.content) == {"user_id": 12}
            return httpx.Response(200, json={"access_token": "token"})
        assert request.headers["Authorization"] == "Bearer token"
        assert request.headers["Idempotency-Key"]
        assert json.loads(request.content) == {"text": "Show snacks"}
        return httpx.Response(200, text="\n\n".join(json.dumps(event) for event in events))

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(respond), base_url="http://eval"
    ) as client:
        assert await answer(client, TurnInput(12, "Show snacks")) == {
            "text": "Showing 1 of 18.",
            "cards": [card],
        }


@pytest.mark.parametrize(
    ("status", "events"),
    [
        (409, []),
        (200, [{"type": "error"}]),
        (200, [{"type": "turn.end", "status": "stopped"}]),
        (200, [{"type": "text.delta", "text": "Incomplete"}]),
        (200, []),
    ],
)
async def test_failed_turn_is_not_returned_for_judging(
    status: int, events: list[dict[str, str]]
) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/demo/sessions":
            return httpx.Response(200, json={"access_token": "token"})
        return httpx.Response(status, text="\n".join(json.dumps(event) for event in events))

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(respond), base_url="http://eval"
    ) as client:
        with pytest.raises(RuntimeError):
            await answer(client, TurnInput(12, "hello"))


async def test_failed_sign_in_does_not_send_a_message() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/demo/sessions"
        return httpx.Response(404, json={"detail": "no user"})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(respond), base_url="http://eval"
    ) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await answer(client, TurnInput(999, "hello"))


@dataclass
class Verdict(Evaluator[TurnInput, Answer, None]):
    outcome: Literal["pass", "fail", "error"]

    def evaluate(self, ctx: EvaluatorContext[TurnInput, Answer, None]) -> bool:
        assert ctx.output["text"].strip() == "A scripted reply."
        if self.outcome == "error":
            raise RuntimeError("judge unavailable")
        return self.outcome == "pass"


@pytest.mark.parametrize(("outcome", "exit_code"), [("pass", 0), ("fail", 1), ("error", 1)])
async def test_full_eval_exit_status_and_case_isolation(
    db_path: Path,
    keys: Keys,
    monkeypatch: pytest.MonkeyPatch,
    outcome: Literal["pass", "fail", "error"],
    exit_code: int,
) -> None:
    settings = make_settings(db_path, keys)
    chat = ScriptedModel([Step(text="A scripted reply.") for _ in answer_quality_eval.CASES])

    def app_for(settings: Settings) -> FastAPI:
        return create_app(settings, chat_model=chat.model, compaction_model=Auxiliary().model)

    cases = [
        Case[TurnInput, Answer, None](
            name=case.name, inputs=case.inputs, evaluators=[Verdict(outcome)]
        )
        for case in answer_quality_eval.CASES
    ]
    assert len({case.inputs.user_id for case in cases}) == len(cases)
    monkeypatch.setattr(answer_quality_eval, "Settings", lambda: settings)
    monkeypatch.setattr(answer_quality_eval, "create_app", app_for)
    monkeypatch.setattr(answer_quality_eval, "CASES", cases)

    assert await answer_quality_eval.main() == exit_code
    assert len(chat.seen) == len(cases)
    # The eval writes only to its copy, even when cases run concurrently.
    with sqlite3.connect(db_path) as db:
        assert db.execute("SELECT count(*) FROM turns").fetchone() == (0,)


def test_database_copy_includes_committed_wal_data(
    db_path: Path, keys: Keys, tmp_path: Path
) -> None:
    with sqlite3.connect(db_path) as source:
        source.execute("PRAGMA journal_mode=WAL")
        source.execute("CREATE TABLE snapshot_check (value TEXT)")
        source.execute("INSERT INTO snapshot_check VALUES ('committed')")
        source.commit()
        copied = tmp_path / "copy"
        copied.mkdir()
        copy_database(make_settings(db_path, keys), copied)
        with sqlite3.connect(copied / "eval.db") as snapshot:
            assert snapshot.execute("SELECT value FROM snapshot_check").fetchone() == ("committed",)
