"""Agent tools: results, shared guard, schemas, and descriptions."""

import json
from pathlib import Path
from typing import Any

import aiosqlite
from pydantic_ai.messages import ModelRequest, ToolReturnPart

from capper.agent.agent import TOOLS
from tests.support import (
    ESTABLISHED_USER,
    GUIDANCE_USER,
    PARALLEL_USER,
    Keys,
    ScriptedModel,
    Seen,
    Step,
    events_of,
    running_app,
)

EXPECTED_TOOLS = {
    "search_products",
    "get_promotions",
    "get_my_referral_code",
    "get_my_purchases",
    "get_popular_products",
    "search_my_history",
    "read_document",
    "show_products",
    "show_promotions",
    "avoid_product",
    "unavoid_product",
    "get_my_avoid_list",
    "add_guidance",
    "update_guidance",
    "remove_guidance",
}


def tool_returns(seen: Seen) -> list[Any]:
    """The tool results the model received in this request, in order."""
    last = seen.messages[-1]
    assert isinstance(last, ModelRequest)
    return [part.content for part in last.parts if isinstance(part, ToolReturnPart)]


async def _call(
    db_path: Path,
    keys: Keys,
    user_id: int,
    calls: list[tuple[str, dict[str, Any]]],
    **overrides: Any,
) -> tuple[list[Any], list[dict[str, Any]], ScriptedModel]:
    chat = ScriptedModel([Step(calls=calls), Step("Done.")])
    async with running_app(db_path, keys, chat, **overrides) as h:
        status, events = await h.send(user_id, "Do the thing.")
        assert status == 200
    return tool_returns(chat.seen[1]), events, chat


def test_the_tool_set_is_exactly_the_fifteen_tools() -> None:
    assert {tool.name for tool in TOOLS} == EXPECTED_TOOLS
    assert all(tool.strict for tool in TOOLS)


async def test_tool_definitions_are_strict_and_describe_paging(db_path: Path, keys: Keys) -> None:
    chat = ScriptedModel([Step("Hi.")])
    async with running_app(db_path, keys, chat) as h:
        await h.send(ESTABLISHED_USER, "Hello")
    definitions = {tool.name: tool for tool in chat.seen[0].info.function_tools}
    assert set(definitions) == EXPECTED_TOOLS
    for tool in definitions.values():
        assert tool.parameters_json_schema.get("additionalProperties") is False, tool.name
        assert "user_id" not in tool.parameters_json_schema.get("properties", {}), tool.name
    for name in ("search_products", "get_promotions", "get_my_purchases", "get_popular_products"):
        description = definitions[name].description or ""
        assert "total_count" in description and "next_cursor" in description, name
    # The read_document schema is a plain string, so it never changes with content.
    name_schema = definitions["read_document"].parameters_json_schema["properties"]["name"]
    assert name_schema["type"] == "string" and "enum" not in name_schema


async def test_list_results_carry_totals_and_cursors(db_path: Path, keys: Keys) -> None:
    returns, _, _ = await _call(
        db_path,
        keys,
        ESTABLISHED_USER,
        [("search_products", {"query": None, "limit": 2, "cursor": None})],
    )
    result = returns[0]
    assert len(result["items"]) == 2
    assert result["total_count"] > 2
    assert result["next_cursor"]


async def test_read_document_reads_the_snapshot_and_refuses_unknown_names(
    db_path: Path, keys: Keys
) -> None:
    returns, _, _ = await _call(
        db_path,
        keys,
        ESTABLISHED_USER,
        [
            ("read_document", {"name": "policy_crisis"}),
            ("read_document", {"name": "scope_charter"}),
        ],
    )
    assert "988" in returns[0]
    assert "no on-demand document named 'scope_charter'" in returns[1]["error"]


async def test_show_products_sends_a_card_built_from_records(db_path: Path, keys: Keys) -> None:
    returns, events, _ = await _call(
        db_path,
        keys,
        ESTABLISHED_USER,
        [("show_products", {"product_ids": [3, 5], "heading": "Ideas"})],
    )
    assert returns[0] == {"shown": 2}
    card = events_of(events, "card")[0]
    assert card["card_type"] == "product"
    assert [item["id"] for item in card["items"]] == [3, 5]
    assert card["items"][0]["name"] == "Macaroni & Cheese Box"


async def test_avoided_products_get_an_error_result_and_no_card(db_path: Path, keys: Keys) -> None:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT id FROM Products WHERE name = 'Peanut Butter'")
        (peanut_butter,) = await cursor.fetchone() or (0,)
    returns, events, _ = await _call(
        db_path,
        keys,
        GUIDANCE_USER,
        [("show_products", {"product_ids": [peanut_butter], "heading": "Ideas"})],
    )
    assert "avoid list" in returns[0]["error"]
    assert not events_of(events, "card")


async def test_calls_past_the_limit_are_not_run_and_tools_are_then_disabled(
    db_path: Path, keys: Keys
) -> None:
    calls: list[tuple[str, dict[str, Any]]] = [("get_my_referral_code", {})] * 3
    chat = ScriptedModel([Step(calls=calls), Step("Done.")])
    async with running_app(db_path, keys, chat, max_tool_calls_per_turn=2) as h:
        await h.send(ESTABLISHED_USER, "Codes please.")
    returns = tool_returns(chat.seen[1])
    assert [r.get("error") for r in returns].count(
        "tool-call limit reached; answer with what you have"
    ) == 1
    settings = chat.seen[1].info.model_settings or {}
    assert settings.get("tool_choice") == "none"


async def test_the_request_limit_backstop_ends_a_runaway_turn(db_path: Path, keys: Keys) -> None:
    looping = [Step(calls=[("get_my_referral_code", {})]) for _ in range(20)]
    chat = ScriptedModel(looping)
    async with running_app(db_path, keys, chat, max_tool_calls_per_turn=2) as h:
        _, events = await h.send(ESTABLISHED_USER, "Loop.")
    assert events[-1]["type"] == "error"


async def test_oversized_results_are_refused_never_cut(db_path: Path, keys: Keys) -> None:
    returns, _, _ = await _call(
        db_path,
        keys,
        ESTABLISHED_USER,
        [("search_products", {"query": None, "limit": 50, "cursor": None})],
        tool_result_max_chars=200,
    )
    assert "result too large" in returns[0]["error"]


async def test_every_call_is_audited_with_free_text_redacted(db_path: Path, keys: Keys) -> None:
    await _call(
        db_path,
        keys,
        ESTABLISHED_USER,
        [
            ("add_guidance", {"text": "Allergic to shellfish.", "expires_at": None}),
            ("search_products", {"query": "secret words", "limit": 1, "cursor": None}),
        ],
    )
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT tool_name, arguments, status FROM tool_calls WHERE user_id = ? ORDER BY id",
            (ESTABLISHED_USER,),
        )
        rows = list(await cursor.fetchall())
    # The two calls run in parallel, so their rows can land in either order.
    arguments = {row[0]: json.loads(row[1]) for row in rows}
    assert set(arguments) == {"add_guidance", "search_products"}
    assert all(row[2] == "ok" for row in rows)
    assert arguments["add_guidance"]["text"] == "[redacted 22 chars]"
    assert arguments["search_products"]["query"] == "[redacted 12 chars]"
    assert "shellfish" not in json.dumps(arguments)


async def test_guidance_expires_at_the_end_of_the_users_local_day(
    db_path: Path, keys: Keys
) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE Users SET time_zone = 'America/Los_Angeles' WHERE id = ?", (ESTABLISHED_USER,)
        )
        await db.commit()
    returns, _, _ = await _call(
        db_path,
        keys,
        ESTABLISHED_USER,
        [("add_guidance", {"text": "Quick dinners this week.", "expires_at": "2030-01-04"})],
    )
    assert returns[0]["saved"]["expires_at"] == "2030-01-04"
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT expires_at FROM guidance_notes WHERE text = 'Quick dinners this week.'"
        )
        (stored,) = await cursor.fetchone() or ("",)
    # 23:59 Pacific on the 4th is the morning of the 5th in UTC.
    assert stored.startswith("2030-01-05T07:59:59")


async def test_tools_act_only_for_the_turns_user(db_path: Path, keys: Keys) -> None:
    returns, _, _ = await _call(
        db_path,
        keys,
        ESTABLISHED_USER,
        [("get_my_referral_code", {}), ("remove_guidance", {"note_id": 1})],
    )
    other, _, _ = await _call(db_path, keys, PARALLEL_USER, [("get_my_referral_code", {})])
    assert returns[0]["code"] != other[0]["code"]
    # Note 1 belongs to GUIDANCE_USER (seed), so it's not found for this user.
    assert returns[1] == {"error": "note 1 not found"}
