"""Shared setup and pass/fail checks for real-model evals."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic_evals.reporting import EvaluationReport
from sqlalchemy.engine import make_url

from capper.config import Settings


@dataclass
class TurnInput:
    user_id: int
    message: str


def check_completed(status_code: int, events: list[dict[str, Any]]) -> None:
    if status_code != 200:
        raise RuntimeError(f"the send failed with HTTP {status_code}")
    last = events[-1] if events else {}
    if last.get("type") != "turn.end" or last.get("status") != "complete":
        raise RuntimeError(f"the turn didn't complete: {last or 'no events'}")


def all_passed(report: EvaluationReport[Any, Any, Any]) -> bool:
    """Failed turns, failed judges, and failed or missing assertions all fail the run."""
    return (
        bool(report.cases)
        and not report.failures
        and not report.report_evaluator_failures
        and all(
            not case.evaluator_failures
            and bool(case.assertions)
            and all(result.value for result in case.assertions.values())
            for case in report.cases
        )
    )


def copy_database(settings: Settings, directory: Path) -> str:
    source = make_url(settings.database_url).database
    if not source or not Path(source).is_file():
        raise SystemExit("no database yet: run `docker compose up` once first (README)")
    target = directory / "eval.db"
    # SQLite's backup includes committed WAL data while the demo is running.
    with sqlite3.connect(source) as original, sqlite3.connect(target) as copied:
        original.backup(copied)
    return f"sqlite+aiosqlite:///{target}"
