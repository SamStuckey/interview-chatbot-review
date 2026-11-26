"""The compaction summary's required headings.

The template is content (`compaction_summary_template`); its `## ` headings
are the required ones. A summary missing any of them is rejected inside the
summarizer run, so it's retried and then fails before it's ever applied.
"""

import re
from dataclasses import dataclass
from typing import Any

from pydantic_ai import ModelRetry, RunContext
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.output import OutputContext

_HEADING = re.compile(r"^##[ \t]+(.+?)[ \t]*$", re.MULTILINE)


def required_headings(template: str) -> list[str]:
    """Every `## ` heading in the template, in order."""
    return [match.group(1) for match in _HEADING.finditer(template)]


def missing_headings(summary: str, headings: list[str]) -> list[str]:
    """The required headings the summary lacks (exact text, any order)."""
    present = {match.group(1).strip().lower() for match in _HEADING.finditer(summary)}
    return [heading for heading in headings if heading.strip().lower() not in present]


@dataclass
class RequireHeadings(AbstractCapability[None]):
    """Attached to the summarizer's own agent: reject a summary that lacks a required heading."""

    headings: list[str]

    async def after_output_process(
        self, ctx: RunContext[None], *, output_context: OutputContext, output: Any
    ) -> Any:
        if isinstance(output, str):
            missing = missing_headings(output, self.headings)
            if missing:
                raise ModelRetry(
                    "The summary is missing these required headings: "
                    + ", ".join(f"'## {heading}'" for heading in missing)
                    + ". Rewrite it with every heading."
                )
        return output
