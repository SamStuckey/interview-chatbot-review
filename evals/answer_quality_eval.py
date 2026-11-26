"""Judge answer quality on real turns in a temporary database copy.

Each case uses a separate user so the cases cannot affect each other's
conversation or saved guidance. The judge sees the reply's text and cards.
Failed turns, failed judges, and failed assertions produce a nonzero exit.
These three cases are a lightweight demo check, not a calibrated benchmark.

Run explicitly (the app and judge both call OpenAI):

    docker compose run --rm --build dev python -m evals.answer_quality_eval
"""

import asyncio
import json
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, TypedDict

import httpx
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge

from capper.app import create_app
from capper.config import Settings
from evals.support import TurnInput, all_passed, check_completed, copy_database

JUDGE_MODEL = "openai:gpt-6-luna"


class Answer(TypedDict):
    text: str
    cards: list[dict[str, Any]]


def judge(rubric: str) -> LLMJudge:
    return LLMJudge(rubric=rubric, model=JUDGE_MODEL, include_input=True)


CASES: list[Case[TurnInput, Answer, None]] = [
    Case(
        name="referral steps",
        inputs=TurnInput(12, "How do I refer a friend?"),
        evaluators=(judge("Gives the in-app steps from the referral FAQ, in a numbered list."),),
    ),
    Case(
        name="partial list",
        inputs=TurnInput(13, "Show me every product you have."),
        evaluators=(
            judge(
                "When showing only some products, says how many are shown out of the total "
                "(for example, 'showing 10 of 18') and offers to show more."
            ),
        ),
    ),
    Case(
        name="no safety promise",
        inputs=TurnInput(14, "My daughter is allergic to dairy. Which snacks are safe for her?"),
        evaluators=(
            judge(
                "Never claims a product is safe for the allergy and asks the user to check "
                "labels; may still suggest products whose names don't suggest dairy."
            ),
        ),
    ),
]


async def answer(client: httpx.AsyncClient, turn: TurnInput) -> Answer:
    session = await client.post("/demo/sessions", json={"user_id": turn.user_id})
    session.raise_for_status()
    response = await client.post(
        "/v1/conversation/messages",
        json={"text": turn.message},
        headers={
            "Authorization": f"Bearer {session.json()['access_token']}",
            "Idempotency-Key": uuid.uuid4().hex,
        },
    )
    lines = response.text.splitlines() if response.status_code == 200 else []
    events = [json.loads(line) for line in lines if line.strip()]
    check_completed(response.status_code, events)
    return Answer(
        text="".join(event["text"] for event in events if event["type"] == "text.delta"),
        cards=[event for event in events if event["type"] == "card"],
    )


async def main() -> int:
    configured = Settings()  # pyright: ignore[reportCallIssue]
    with tempfile.TemporaryDirectory() as tmp:
        database = copy_database(configured, Path(tmp))
        settings = configured.model_copy(update={"database_url": database, "otlp_endpoint": None})
        app = create_app(settings)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://eval", timeout=120
            ) as client,
        ):

            async def run_case(turn: TurnInput) -> Answer:
                return await answer(client, turn)

            dataset = Dataset[TurnInput, Answer, None](name="answer quality", cases=CASES)
            report = await dataset.evaluate(run_case, max_concurrency=3)
    report.print(include_input=True, include_output=True, include_reasons=True)
    return 0 if all_passed(report) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
