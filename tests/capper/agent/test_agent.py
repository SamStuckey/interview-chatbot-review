"""Shared request settings and the per-user cache key."""

from pathlib import Path

from capper.agent.agent import base_model_settings, opaque_user_key, run_model_settings
from tests.support import Keys, make_settings


def test_base_settings(tmp_path: Path, keys: Keys) -> None:
    settings = base_model_settings(make_settings(tmp_path / "x.db", keys))
    assert settings == {
        "openai_reasoning_context": "current_turn",
        "openai_send_reasoning_ids": False,
        "openai_truncation": "disabled",
        "cache": True,
        "max_tokens": 4096,
    }


def test_the_cache_key_is_opaque_and_per_user() -> None:
    first, second = opaque_user_key("s", 1), opaque_user_key("s", 2)
    assert run_model_settings(first) == {"openai_prompt_cache_key": first}
    assert first != second and first != "1" and len(first) == 64
    assert opaque_user_key("other-secret", 1) != first
