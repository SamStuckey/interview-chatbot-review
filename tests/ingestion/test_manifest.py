"""The manifest is an allowlist, and the authored content set is complete."""

from pathlib import Path

import pytest

from ingestion import load_manifest, normalize, read_sources
from tests.support import MANIFEST

EXPECTED = {
    "scope_charter",
    "persona_voice",
    "do_no_harm_core",
    "policy_allergens_food_safety",
    "policy_dietary_medical_claims",
    "policy_child_safety",
    "policy_product_misuse",
    "policy_crisis",
    "referral_faq",
    "program_rules",
    "product_knowledge",
    "greeting",
    "compaction_summary_template",
}


def test_the_manifest_lists_exactly_the_authored_documents() -> None:
    assert {entry.name for entry in load_manifest(MANIFEST)} == EXPECTED


def test_the_core_lists_every_on_demand_policy() -> None:
    sources = {s.name: s for s in read_sources(MANIFEST)}
    on_demand = {name for name, s in sources.items() if s.load == "on_demand"}
    core = sources["do_no_harm_core"].body
    assert on_demand and all(f"`{name}`" in core for name in on_demand)


def test_only_listed_files_are_read(tmp_path: Path) -> None:
    (tmp_path / "listed.md").write_text("Listed.\n")
    (tmp_path / "secret.md").write_text("Internal only.\n")
    manifest = tmp_path / "manifest.toml"
    manifest.write_text(
        '[[documents]]\nname = "listed"\nclass = "user_knowledge"\nload = "always"\n'
        'file = "listed.md"\n'
    )
    assert [s.name for s in read_sources(manifest)] == ["listed"]


def test_unknown_classes_loads_and_duplicates_are_refused(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.toml"
    entry = '[[documents]]\nname = "a"\nclass = "{c}"\nload = "{l}"\nfile = "a.md"\n'
    for text in (
        entry.format(c="secret", l="always"),
        entry.format(c="user_knowledge", l="sometimes"),
        entry.format(c="user_knowledge", l="always") * 2,
    ):
        manifest.write_text(text)
        with pytest.raises(ValueError):
            load_manifest(manifest)


def test_normalize_drops_author_notes_and_cosmetic_whitespace() -> None:
    body = "<!-- a note\nfor authors -->\n# Title  \r\n\r\n\r\n\r\nText\n\n\n"
    assert normalize(body) == "# Title\n\nText\n"
    assert normalize(body) == normalize(body.replace("Title  ", "Title"))
