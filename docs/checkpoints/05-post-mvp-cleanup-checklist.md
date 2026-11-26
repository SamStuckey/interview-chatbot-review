# Post-MVP Cleanup

Work to do before submission, sorted out of `checkpoints/04-post-mvp-agentic-adversarial-cleanup.md`
one item at a time (2026-11-18). Each entry keeps its number from that list.

## 1. Remove the auxiliary safety check from the MVP

Every new turn currently waits for a separate model to select safety policies
while the service loads account and conversation data. The tuned check took
roughly one second at the median in the build log, with a two-second timeout.
Sam decided to remove this check and its supporting cruft from the MVP.

- Remove the check from `TurnRunner` and the app factory. Delete the checker,
  its model settings and timeout configuration, and the request-context code
  that injects preselected policies. Keep the auxiliary model for compaction.
- Remove the classifier prompt and its manifest entry. Verify that publishing
  the updated manifest deactivates the previously published prompt. Keep the
  always-on do-no-harm instructions, the detailed policies, and `read_document`.
- Remove checker-specific trace attributes, tests, test doubles, and eval
  injection. Keep time-to-first-text telemetry and the policy lookup eval.
- Reconcile current descriptions of request flow and privacy with the removal.
  Preserve historical design and measurement records.
- Verify that ordinary turns go straight to the chat agent after context is
  ready and that safety-sensitive turns can still load the relevant policy.

## 3. Make the policy lookup eval fail correctly

In `evals/tool_call_eval.py`, require a successful HTTP response and a terminal
`turn.end` with `status: complete` before grading policy reads. An error,
stopped turn, or missing terminal event must fail the case, including cases
that expect zero reads. Query only `read_document` audit rows with
`status = 'ok'` so a failed lookup cannot satisfy a case. Keep printing the
report and return a nonzero exit code if any case fails or cannot run.

Verify that an errored referral turn fails, an unsuccessful expected policy
read does not count, failing or unrunnable cases exit nonzero, and an
all-passing report exits zero. Keep the eval focused on policy retrieval.

## 5. Add an optional date range to `search_my_history`

Extend the existing tool so Capper can retrieve older messages by date alone
or narrow a keyword search to a date range. Preserve keyword-only behavior
when dates are omitted. Apply the date and verified-user filters in the
database before selecting matches. Keep results bounded to five. For date-only
lookups, return results in a deterministic chronological order and make the
ordering and range boundaries explicit in the tool description. Use the
user's time zone from item 36 to interpret calendar days, then compare with
stored UTC timestamps. Validate invalid and reversed ranges.

Verify keyword-only search, date-only retrieval after compaction, combined
keyword and date filtering, date boundaries, and account isolation. Use
“What did we talk about last Tuesday?” as the date-only example.

## 7. Disable demo account switching during a reply

The demo clears the chat on sign-out but keeps processing the prior reply's
stream. A late card can appear in the next demo user's chat. Use the simplest
fix. Disable the demo's account-switch control while `state.sending` is true
and re-enable it when the existing send cleanup runs. Verify switching is
unavailable during a reply and available again after completion, Stop, or a
stream failure.

## 12. Review MVP tracing for simplicity and consistency

Review the turn, model, and tool traces together. Keep naming, attributes,
and configuration consistent across the demo paths. Keep the detail needed
to follow a turn and diagnose failures. Remove redundant instrumentation,
unused configuration, and trace fields left over from removed features.
Verify a representative turn in Jaeger after the cleanup.

## 13. Review MVP reliability and usage limits

Review the defaults for retries, timeouts, model requests, tool calls, output
tokens, and one active turn per user. Verify that the existing limits work
as intended and keep the defaults simple enough to explain in the demo.
Successive turns after a previous turn finishes are expected behavior. Daily
quotas and spending caps are future considerations.

## 16. Trace loaded and saved summary IDs separately from compaction

Record the loaded summary row ID when history is read and the new summary
row ID only after its transaction commits. Each persisted row already holds
its cutoff. Carry the loaded ID through `StoredHistory` and return the saved
ID from persistence so the runner can record these events accurately.

Keep compaction execution as a separate trace event based on the existing
after-run inspection. Record the previous and new cutoff when known, or a
clearly labeled numeric position or count when the boundary cannot yet be
mapped to a database message ID. Preserve visibility into compaction with an
unresolved boundary or failed persistence. Keep summary and message text out
of the trace.

## 19. Verify safe diagnostics for context-limit failures

Exercise a provider context-limit rejection with a controlled fixture. Verify
the trace identifies the failure category, turn, and model, with context
usage and budget details where available. The generic exception path does
not set a dedicated failure category and logs a traceback, so check the
actual log and span for provider error text that could expose message
content. Add sanitized metadata where missing and keep the client error
generic. Pre-send token estimation and provider-side truncation remain
outside MVP scope.

## 27. Manage avoided products by text without injecting the list

Remove the avoided-product list from routine prompt context. Keep the
user's avoid associations as the source of truth for server-side exclusion
from recommendation results and cards.

Support text matching for both directions. For “don't show me X,” resolve
the catalog product and add its avoid association. For “take X off my avoid
list,” match against the authenticated user's saved avoid entries and delete
the association. Preserve ID-based removal as an available path. Ask for
clarification when text matching leaves multiple plausible candidates, and
report no match without changing records. Verify both removal paths and
that unrelated turns no longer receive the avoid list. Keep historical
messages intact.

## 31. Check for unused confirmation scaffolding

Inspect the tool and streaming paths for unused pending-action code, event
types, configuration, or branches left over from the confirmation design.
Remove anything that exists solely for an unimplemented confirmation flow.
Preserve the existing behavior for user-requested memory and avoid-list
changes, including clarification when the requested item is ambiguous.

## 36. Use the user's time zone for local dates and times

Keep storing timestamps in UTC. Add an optional IANA time-zone column to
the Users table and expose it through the authenticated profile. Use that
zone for the model's local-time context and for interpreting calendar-day
filters in item 5. Convert local date boundaries to UTC before querying.
Use the configured default for existing users without a time zone. Validate
zone names and verify local-day boundaries across daylight-saving changes.
