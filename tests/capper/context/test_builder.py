"""Pure context assembly: placement of the request-only blocks."""

from datetime import UTC, datetime

from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

from capper.context.builder import (
    AccountView,
    NoteView,
    account_context_request,
    account_context_text,
    turn_context_request,
)
from capper.context.inject import insert_request_context


def test_account_context_carries_notes_and_dates_but_not_the_avoid_list() -> None:
    text = account_context_text(
        AccountView(
            "Ana",
            "Hilltop",
            [
                NoteView(1, "Likes pasta.", "2026-11-01", None),
                NoteView(2, "No sauces.", "2026-11-02", "2026-12-01"),
            ],
        )
    )
    assert text.index("Likes pasta.") < text.index("No sauces.")
    assert '"expires_on": "2026-12-01"' in text and "avoid" not in text


def test_blocks_go_first_and_right_before_the_prompt() -> None:
    old = ModelRequest(parts=[UserPromptPart("old")])
    reply = ModelResponse(parts=[TextPart("hi")])
    prompt = ModelRequest(parts=[UserPromptPart("new")])
    account = account_context_request(AccountView("Ana", None, []))
    turn = turn_context_request(datetime(2026, 11, 17, tzinfo=UTC))
    out = insert_request_context([old, reply, prompt], account=account, turn=turn, prompt=prompt)
    assert out == [account, old, reply, turn, prompt]


def test_the_prompt_is_found_after_the_run_adds_messages() -> None:
    prompt = ModelRequest(parts=[UserPromptPart("new")])
    later = ModelResponse(parts=[TextPart("calling a tool")])
    account = account_context_request(AccountView("Ana", None, []))
    turn = turn_context_request(datetime(2026, 11, 17, tzinfo=UTC))
    out = insert_request_context([prompt, later], account=account, turn=turn, prompt=prompt)
    assert out == [account, turn, prompt, later]
