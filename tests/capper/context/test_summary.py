"""Required summary headings come from the template."""

from capper.context.summary import missing_headings, required_headings
from tests.support import ROOT


def test_headings_come_from_the_template() -> None:
    template = (ROOT / "content/source/compaction_summary_template.md").read_text()
    headings = required_headings(template)
    assert headings == [
        "Goals and constraints the user stated",
        "IDs mentioned",
        "What happened",
        "Open questions",
    ]
    complete = "\n".join(f"## {h}\nNone." for h in headings)
    assert missing_headings(complete, headings) == []
    assert missing_headings("## IDs mentioned\nNone.", headings) == [
        "Goals and constraints the user stated",
        "What happened",
        "Open questions",
    ]
