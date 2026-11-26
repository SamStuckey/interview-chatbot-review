"""Policy eval grading: completed turns, successful reads, and failure exit status."""

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from pydantic_evals import Case, Dataset

from evals.tool_call_eval import (
    ReadsTheRightPolicy,
    TurnInput,
    all_passed,
    check_completed,
    successful_reads,
)

START = {"type": "turn.start", "turn_id": "t1", "user_message_id": "m1"}


@pytest.mark.parametrize(
    ("status_code", "events"),
    [
        (409, []),
        (200, [START, {"type": "error", "code": "generic", "message": "..."}]),
        (200, [START, {"type": "turn.end", "status": "stopped", "assistant_message_id": None}]),
        (200, [START]),
    ],
)
def test_a_turn_that_did_not_complete_fails_its_case(
    status_code: int, events: list[dict[str, Any]]
) -> None:
    with pytest.raises(RuntimeError):
        check_completed(status_code, events)


def test_a_completed_turn_is_graded() -> None:
    check_completed(200, [START, {"type": "turn.end", "status": "complete"}])


def test_only_successful_reads_count(tmp_path: Path) -> None:
    path = tmp_path / "eval.db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE tool_calls (turn_id, tool_name, arguments, status)")
        db.executemany(
            "INSERT INTO tool_calls VALUES (?, ?, ?, ?)",
            [
                ("t1", "read_document", json.dumps({"name": "policy_crisis"}), "ok"),
                ("t1", "read_document", json.dumps({"name": "policy_child_safety"}), "error"),
                ("t1", "search_products", json.dumps({"query": "x"}), "ok"),
                ("t2", "read_document", json.dumps({"name": "policy_product_misuse"}), "ok"),
            ],
        )
    assert successful_reads(str(path), "t1") == ["policy_crisis"]


async def test_the_exit_code_follows_every_case() -> None:
    async def report_for(task_output: list[str] | None) -> bool:
        async def task(_turn: TurnInput) -> list[str]:
            if task_output is None:
                raise RuntimeError("the turn didn't complete")
            return task_output

        dataset = Dataset[TurnInput, list[str], None](
            name="grading",
            cases=[Case(inputs=TurnInput(1, "hi"), expected_output=[])],
            evaluators=[ReadsTheRightPolicy()],
        )
        return all_passed(await dataset.evaluate(task, progress=False))

    assert await report_for([]) is True
    assert await report_for(["policy_crisis"]) is False
    assert await report_for(None) is False
