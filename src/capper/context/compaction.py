"""Clearing and compaction on the Harness, and finding a compaction's watermark.

`ClearToolResults` runs first; then, at the same token trigger, the summarizer
summarizes with our template. No other strategy follows, so a failed summary
fails the turn. After a run, the service locates the new
summary and the kept suffix by position.
"""

from collections.abc import Sequence
from dataclasses import dataclass, replace

from pydantic_ai import RunContext
from pydantic_ai.messages import CompactionPart, ModelMessage, ModelRequest
from pydantic_ai.models import Model
from pydantic_ai_harness.compaction import ClearToolResults, SummarizingCompaction

from capper.agent.deps import CapperDeps
from capper.context.summary import RequireHeadings, required_headings

SUMMARY_METADATA_KEY = "pydantic-ai-harness.compaction.summary.v1"
# Set explicitly, so the trace's "cleared" check can't drift from the Harness's default.
CLEARED_PLACEHOLDER = "[tool result cleared]"
TEMPLATE_DOCUMENT = "compaction_summary_template"


class SummaryTemplateMissing(RuntimeError):
    """The content snapshot has no summary template, so compaction can't run."""


@dataclass
class TemplateSummarizer(SummarizingCompaction[CapperDeps]):
    """The Harness summarizer, with its prompt and heading check taken from the turn's snapshot.

    The template is content, so a new template applies on
    the next turn without a restart. Its `## ` headings are required.
    """

    async def compact(
        self, messages: list[ModelMessage], ctx: RunContext[CapperDeps]
    ) -> list[ModelMessage]:
        template = ctx.deps.snapshot.get(TEMPLATE_DOCUMENT)
        if template is None:
            raise SummaryTemplateMissing(f"content has no active {TEMPLATE_DOCUMENT!r}")
        configured = replace(
            self,
            summary_prompt=template.body,
            summarization_capabilities=[RequireHeadings(required_headings(template.body))],
        )
        return await super(TemplateSummarizer, configured).compact(messages, ctx)


@dataclass(frozen=True)
class CompactionLimits:
    trigger_tokens: int
    keep_tokens: int
    keep_pairs: int
    min_clear_tokens: int


def build_clearing(limits: CompactionLimits) -> ClearToolResults[CapperDeps]:
    """Clear old tool results in place, keeping the active turn and five past results."""
    return ClearToolResults(
        max_tokens=limits.trigger_tokens,
        keep_pairs=limits.keep_pairs,
        clear_tool_inputs=False,
        min_clear_tokens=limits.min_clear_tokens,
        placeholder=CLEARED_PLACEHOLDER,
    )


def build_compaction(limits: CompactionLimits, model: Model | str) -> TemplateSummarizer:
    """Summarize at the trigger, keeping at least `keep_tokens` verbatim."""
    return TemplateSummarizer(
        model=model,
        max_tokens=limits.trigger_tokens,
        keep_tokens=limits.keep_tokens,
        preserve_first_user_message=False,
        keep_user_messages=False,
        retries=1,
    )


def summary_part(message: ModelMessage) -> CompactionPart | None:
    if isinstance(message, ModelRequest):
        for part in message.parts:
            if (
                isinstance(part, CompactionPart)
                and part.metadata is not None
                and part.metadata.get(SUMMARY_METADATA_KEY) is True
            ):
                return part
    return None


@dataclass(frozen=True)
class CompactionResult:
    """A compaction found after a run: the summary message, and where the kept suffix starts."""

    summary: ModelRequest
    text: str
    first_kept: int
    """Index into `loaded + new` of the first message kept verbatim."""


class CompactionShapeError(RuntimeError):
    """The run's history doesn't have the `[summary, *suffix]` shape persistence relies on."""


def find_compaction(
    loaded: Sequence[ModelMessage], new: Sequence[ModelMessage], final: Sequence[ModelMessage]
) -> CompactionResult | None:
    """Locate a compaction made during the run, by position.

    `loaded` is the history the run started from (it may begin with an earlier
    summary), `new` the run's new messages, `final` the run's resulting
    history. Our configuration compacts to `[summary, *suffix]`, where the
    suffix is a tail of `loaded + new`. If `final` starts with the summary the
    run loaded, nothing was compacted. Anything else is an error, never a guess.
    """
    if not final:
        return None
    part = summary_part(final[0])
    if part is None:
        if any(summary_part(m) for m in final):
            raise CompactionShapeError("a summary appears after the start of the history")
        return None
    loaded_part = summary_part(loaded[0]) if loaded else None
    if loaded_part is not None and (part is loaded_part or part == loaded_part):
        return None
    full = [*loaded, *new]
    kept = len(final) - 1
    first_kept = len(full) - kept
    if not 0 < first_kept <= len(full):
        raise CompactionShapeError("the kept suffix doesn't fit the run's messages")
    if new and list(final[-len(new) :]) != list(new):
        raise CompactionShapeError("the run's new messages aren't the end of its history")
    assert isinstance(final[0], ModelRequest)
    return CompactionResult(summary=final[0], text=part.content or "", first_kept=first_kept)
