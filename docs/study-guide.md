# Project Study Guide

Notes on the concepts and patterns used in this project, with Rails and
JavaScript comparisons where useful.

## Evaluator

An **evaluator** is a grading rule. `Evaluator` is the base class supplied by
Pydantic Evals, our eval library. We inherit from it and implement `evaluate()`
to define what counts as a pass. It is a library interface, not a Python
language feature. The closest RSpec comparison is a custom matcher.

### How we use it

In [tool_call_eval.py](../evals/tool_call_eval.py), each case contains a user
message and the policy documents we expect the agent to read. The task runs
the conversation and returns the names of policies successfully read, taken
from the tool audit records. The library then calls our evaluator with that
result and the case's expectations.

```python
@dataclass
class ReadsTheRightPolicy(Evaluator[TurnInput, list[str], None]):
    def evaluate(self, ctx: EvaluatorContext[TurnInput, list[str], None]) -> bool:
        expected = ctx.expected_output or []
        if not expected:
            return ctx.output == []
        return all(name in ctx.output for name in expected)
```

For an allergy question, the expected policy is
`policy_allergens_food_safety`. The evaluator passes if that policy appears
in the successful reads. Additional policy reads are allowed in this case.
When no policy is expected, it passes only if no policies were read.

The agent making the tool choices uses a real model, but this grading rule
is ordinary, deterministic Python. Separately, `LLMJudge` in
[answer_quality_eval.py](../evals/answer_quality_eval.py) uses a model to grade
replies against written criteria. Evaluators do not inherently require an LLM.

### Reading the syntax

| Syntax | Meaning |
| --- | --- |
| `class ReadsTheRightPolicy(Evaluator[...])` | Defines a subclass of `Evaluator`, like Ruby's `< Evaluator` or JavaScript's `extends Evaluator`. |
| `[TurnInput, list[str], None]` | Generic type parameters: the task's input type, output type, and metadata type. This eval uses no metadata. |
| `@dataclass` | A class decorator that generates standard methods such as initialization, representation, and equality from declared fields. Our evaluator declares no fields. |
| `ctx: EvaluatorContext[...]` | A type annotation for the context containing the case's input, actual output, and expected output. |
| `-> bool` | A return type annotation: this method returns `True` or `False`. |

The generic parameters and annotations describe types; they are not
constructor arguments or automatic runtime validation.

### Why the class lives beside the cases

Python allows several classes and functions in a single module. Keeping a
small evaluator beside the cases that use it is a normal pattern and makes
the eval easy to read. Rails more often puts named application classes in
separate files under its autoloading conventions. If multiple eval files
need the same grading rule, we can move it into a shared module.

### Suggested interview answer

“We use Pydantic Evals to run cases and grade the results. Our custom evaluator
checks the tool audit records to confirm that the agent read the expected
policy. That check is deterministic. We separately use an LLM judge for
subjective answer-quality checks.”

## Python async and coroutines

`async def` defines a **coroutine function**. Calling it creates a coroutine
object describing work to run; the function's body has not started yet.
Awaiting the coroutine runs it and gives back its eventual result.

```python
async def main() -> int:
    response = await client.get("/products")
    return response.status_code
```

`await` lets the function suspend when the operation needs to wait. The
event loop can then run other ready tasks, such as handling another request
while this one waits for a database or model response. When the operation
finishes, the function resumes. An awaitable that is already ready may
complete without suspending.

`async` and `await` are Python language syntax; `asyncio` is the standard
library that provides the event loop and task scheduling used here.

### Compared with JavaScript

| Behavior | JavaScript | Python with asyncio |
| --- | --- | --- |
| Define an async function | `async function main()` | `async def main()` |
| Calling it returns | A Promise | A coroutine object |
| Calling it starts its body | Yes, immediately, until its first suspension | No; await it or schedule it |
| Obtain its eventual result | `await promise` | `await coroutine` or `await task` |
| Schedule work and await it later | Call the async function and keep its Promise | Use `asyncio.create_task()` and keep its Task |

You can pass around a coroutine or Task before the result is available,
but you cannot use its eventual value until it has completed. The same
distinction applies to a JavaScript Promise and its resolved value.

### Awaiting versus scheduling

Inside an async function:

```python
pending = main()          # Creates a coroutine; does not start its body.
result = await pending   # Runs it and eventually produces an integer.
```

To schedule it while the current function continues:

```python
task = asyncio.create_task(main())
# Continue other work; the task can run when control returns to the event loop.
result = await task
```

The `-> int` annotation describes the eventual result after awaiting, rather
than the coroutine object returned by the initial call. Return annotations
are optional in Python, but our project requires them and checks them with
Pyright.

### Async does not create a thread

An asyncio event loop runs tasks cooperatively on its thread: one task
executes Python code at a time, and other tasks get a turn when it yields
control. This supports concurrent I/O without needing a thread per request.
It does not automatically make CPU-heavy work run in parallel.

Blocking calls still block the event loop, even inside `async def`. For
example, use `await asyncio.sleep(1)` for an async delay; `time.sleep(1)`
blocks that thread. Blocking work needs a suitable thread or process
executor when it must run without blocking the event loop.

### How our eval starts

At the script's entry point, our eval uses:

```python
sys.exit(asyncio.run(main()))
```

`main()` creates the coroutine. `asyncio.run()` creates an event loop, runs
the coroutine to completion, and returns its integer result. `sys.exit()`
uses that result as the process exit code: `0` means success, and `1` means
the eval failed. This entry-point pattern is for a standalone script;
inside an existing async function, use `await` instead.

### Suggested interview answer

“Python async uses coroutines and an event loop to overlap waiting for I/O.
An async function can suspend at an await so other tasks can run. This is
similar to JavaScript async/await, but calling a Python coroutine function
does not start it; it must be awaited or scheduled. Async does not
automatically create threads or parallelize CPU work.”

## Context managers: `with` and `async with`

A **context manager** defines setup and cleanup around a block of code.
Python's `with` statement uses that behavior to manage resources such as
files, temporary directories, and HTTP clients.

### Reading our temporary-directory example

```python
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    database = Path(tmp) / "eval.db"
    # Use the temporary directory here.

# The directory and its contents have been deleted.
```

`TemporaryDirectory()` creates the temporary directory and its manager.
Entering the context provides the directory's path, which `as tmp` assigns
to the variable. Exiting the block triggers cleanup, including when the
block raises an exception or returns early. An exception normally continues
after cleanup; a context manager can explicitly choose to suppress it.

The value after `as` is whatever the manager provides when entering the
context. It is not necessarily the manager itself: here it is a path string.

### Resource lifetime versus variable scope

`with` does not create a new variable scope in Python. Inside a function,
`tmp` remains accessible after this block, but the directory it names has
been deleted. The block controls resource lifetime, not variable scope.

The closest Ruby equivalent is:

```ruby
require "tmpdir"

Dir.mktmpdir do |tmp|
  # Use the temporary directory here.
end
# The directory has been removed.
```

Ruby's block parameter is local to its block; Python's `as tmp` binding does
not have that same scope rule. In JavaScript, explicit resource cleanup is
often expressed with `try`/`finally`; Python's context manager packages that
pattern for reuse.

### Async context managers in our eval

```python
async with (
    app.router.lifespan_context(app),
    httpx.AsyncClient(transport=transport, base_url="http://eval") as client,
):
    # The app is started and the HTTP client is available.
    ...
```

`async with` follows the same setup-and-cleanup pattern, but allows entering
and exiting the context to await asynchronous operations. It does not
create a thread or automatically run the block in the background.

The contexts enter in order: start the app, then enter the HTTP client's
context. They exit in reverse order: close the client, then shut down the
app. The parentheses let us write multiple contexts across several lines;
this behaves like nested `async with` blocks.

### Suggested interview answer

“A Python context manager handles setup and cleanup around a block using
`with`. Our eval uses one to remove its temporary database directory and
async context managers to manage the app and HTTP client. Cleanup runs when
the block exits, including on exceptions. The block manages resource
lifetime rather than creating a variable scope.”

## Stateless resource server: authentication

A **resource server** is the API that protects application resources, such
as a user's conversation and saved guidance. An **authorization server**
issues the access tokens that clients present to that API.

Capper acts as a **stateless resource server** for authentication: each
protected request carries its own bearer token, and Capper verifies it
without looking up a stored login session or asking the token issuer to
validate it on every request.

```http
Authorization: Bearer <access token>
```

### How our JWT verification works

The issuer signs the JWT with a private key. Capper uses the corresponding
public key to verify its signature and checks the token's claims:

| Claim | Meaning | Our check |
| --- | --- | --- |
| `sub` | Subject: the user's identity | Parse as a user ID and confirm that user exists. |
| `exp` | Expiration time | Reject an expired token. |
| `iss` | Issuer | Require the configured token issuer. |
| `aud` | Audience: the intended recipient | Require the configured audience. |

Our verifier accepts only the configured signing algorithm, RS256, and
requires all four claims. A valid signature alone is insufficient.

The verified user ID then scopes application queries. Authentication
establishes identity; the application still enforces which records that
identity can access.

### Where this lives in our app

| Code | Role |
| --- | --- |
| `auth/service.py`: `TokenVerifier` | Verifies incoming JWTs and returns the user ID. |
| `auth/api.py`: `CurrentUser` | Supplies that verified ID to protected FastAPI routes. |
| `auth/service.py`: `DemoSessionIssuer` | Signs demo JWTs, standing in for an external issuer. |
| `demo/api.py`: `POST /demo/sessions` | Lets the demo client obtain a token for a selected account. |

With an external authentication service, that service would issue the
tokens. Capper would continue verifying incoming tokens using the trusted
issuer's public key and configured claims.

### What “stateless” does and does not mean

Capper keeps no per-token login session that must be loaded to authenticate
each request. It still checks user existence in the database and stores
application state, including conversations, preferences, and purchases.
“Stateless” here describes authentication, not the entire application.

This is an architecture pattern rather than a Python feature. A Rails or
JavaScript API can use the same JWT verification approach. JWTs are signed,
not necessarily encrypted: their claims should not be treated as secret.

### Suggested interview answer

“Capper acts as a stateless resource server. Protected requests carry a
signed JWT, which we verify locally using the issuer's public key. We check
expiration, issuer, audience, and user identity, then scope data access to
that user. The demo includes a token issuer to stand in for external auth;
the API's verification path works independently of that demo sign-in.”

## Ruff: linting and formatting

**Ruff** checks Python code for common mistakes and applies a consistent
style. It is a development tool, not part of handling application requests.
The closest familiar Rails tool is RuboCop.

Ruff has two main jobs:

| Command | Purpose |
| --- | --- |
| `ruff check` | Run configured lint rules, including unused imports, undefined names, and import ordering. |
| `ruff format --check` | Report files whose formatting differs from the formatter's output, without changing them. |
| `ruff format` | Rewrite Python files into the standard format. |

Our configuration is in `pyproject.toml`. It targets Python 3.14, uses a
100-character line length, and enables selected rules for errors, imports,
modern syntax, async code, and simplification. Formatting applies to Python;
Markdown prose is outside its scope here.

From the repo root:

```bash
docker compose run --rm dev ruff check
docker compose run --rm dev ruff format --check
```

### Suggested interview answer

“We use Ruff for Python linting and formatting. It catches common mistakes
and keeps code style consistent, so reviewers can focus on behavior rather
than formatting.”

## Pyright: static type checking

**Pyright** checks that code uses types consistently without running the
application. It reads annotations such as `query: str | None` and
`-> list[HistoryMatch]`, and also infers types from assignments and usage.
It is comparable to TypeScript's type checker or Ruby's Sorbet.

For example:

```python
def product_count() -> int:
    return "five"  # Pyright reports a string where an integer is promised.
```

It can also catch missing arguments, incorrect keyword names, access to
nonexistent attributes, and using a possibly absent value before checking
for `None`. Our project enables strict checking in `pyproject.toml` across
application code, scripts, tests, evals, and migrations.

```bash
docker compose run --rm dev pyright
```

Python itself does not enforce these annotations at runtime. Pyright checks
the code's type contracts; runtime validation still handles incoming data.
Ruff, Pyright, and pytest complement one another: lint and formatting checks,
type checks, and tests of actual behavior.

### Suggested interview answer

“We use Pyright in strict mode to check Python type contracts before running
the code. It catches mismatched return values, incorrect calls, and unsafe
handling of optional values. It complements runtime validation and tests.”

## Why we use async SQLAlchemy sessions

A SQLAlchemy **session** tracks ORM objects and changes and coordinates
database access and transactions for a unit of work. It is separate from
an authentication session or JWT.

Capper's requests, model calls, and streaming run asynchronously. Using
SQLAlchemy's `AsyncSession` lets database operations participate in that
same flow: while a query waits, the event loop can handle other ready tasks
instead of blocking on a synchronous database call.

### The database is still a local file

SQLite reads and writes a local file, but disk access and waiting for locks
can still take time. Our `sqlite+aiosqlite` driver runs SQLite operations on
a worker thread per connection and lets the event loop await their results.
The async interface makes that waiting cooperative; it does not make every
query faster or remove SQLite's limit of one writer at a time.

### How our session factory is used

`src/capper/db.py` constructs an async engine and a session factory. Services
receive that factory and create a session for each short unit of database
work:

```python
async with self._sessions() as session:
    user = await repository.get_user(session, user_id)
```

The factory is shared; the individual session is not shared across concurrent
tasks. Sessions contain mutable transaction and ORM state, so unrelated
operations need their own sessions. Exiting the context closes the session
and releases its database resources.

For an explicit write transaction, our audit log uses:

```python
async with self._sessions() as session, session.begin():
    await repository.add_tool_call(session, record)
```

`session.begin()` commits on successful exit and rolls back if the block
raises an exception. A session context by itself does not automatically
commit writes.

We close each transaction as soon as its database work is done. A conversation
turn can perform several database operations, but it does not hold one
transaction open for the whole model call or response stream. This reduces
lock contention during a potentially long generation. The factory
uses `expire_on_commit=False`, which keeps loaded attributes available after
commit without requiring an automatic reload.

### Compared with Rails

Active Record usually hides connection and transaction management behind
model methods. Here, SQLAlchemy makes the unit of database work explicit
with a session, and its async API uses `await` for database I/O. Both
approaches still need clear transaction boundaries.

### Suggested interview answer

“We use async SQLAlchemy sessions so database waits cooperate with the same
event loop that handles requests and model streaming. Each unit of work gets
its own session, and transactions stay short. SQLite is still a local file;
aiosqlite performs its database operations on worker threads so they do not
block the event loop.”



# Future Considerations

Things to think about, plan to talk about, and possibly document further:
outside the MVP's build. These are **not** decisions (those go in
`decision-log.md`).

Rebuilt on 2026-11-18. Items are added here one at a time as
`checkpoints/04-post-mvp-agentic-adversarial-cleanup.md` is sorted. Every open item from the
previous version is in that list; the previous text is in git (`9e43cf9`).

## 1. Revisit auxiliary safety routing before the presentation

Review when a separate policy-selection model is worth adding. The MVP
relies on the always-on do-no-harm instructions and the
main agent's `read_document` tool. The auxiliary check could preload detailed
policies before the first chat request, but every new turn waited for it.
After tuning, the build log reported roughly one second at the median,
with a configured two-second timeout. On timeout the main agent still had
its core instructions and policy lookup.

Compare the main-agent-only flow with preloading all five current policies
or using a separate classifier. Consider what evidence would justify the
extra call, particularly policy selection and answer quality on ambiguous
follow-ups whose safety context is in earlier messages. The auxiliary check
only saw the newest message. Review latency alongside those outcomes before
deciding how to present the trade-off.

## 2. Deployment security and published ports

Docker packages the proof of concept so reviewers can run it with fake data.
The current build is for demos only. Compose publishes the app and Jaeger
UI ports on the host. Where the network permits access, another device can
reach the demo sign-in and trace viewer. The demo sign-in can issue a token
for any demo account, and live chat requests use the configured API quota.
Deployment hardening is outside MVP cleanup.

For a future deployment design, decide who needs access to the app, the
trace viewer, and the collector. Consider loopback bindings for a local demo
where appropriate. For a real deployment, remove the demo sign-in,
integrate the existing Carton Caps identity service, and restrict access to
the service and trace infrastructure according to their intended audiences.

## 8. Investigate cost attribution on turns that compact history

The MVP keeps its current trace estimate. It applies the chat model's rates
to aggregate turn usage, which can overstate the cost of compaction when the
summarizer uses a cheaper model. Investigate whether usage can be attributed
per model or per request, including cached input tokens. Compare calculating
a blended turn estimate from that breakdown with retaining the current
approximation for diagnostics.

## 9. Discuss conversation sessions in the presentation

The MVP uses one continuous conversation per user. For the presentation,
consider when grouping turns by inactivity would be useful for analytics and
when an explicit New Chat action would be useful for separate transcripts.
If discussing separate chats, explain what context could carry across them.

## 10. Discuss database scaling for a real client

SQLite serves the single-instance demo. For the presentation, explain when
write contention or multiple Capper instances would justify moving to a
managed database. Compare using the client's database with clear table
ownership and giving Capper its own database with API access to client data.
Discuss how to migrate Capper's schema and data, including replacing
SQLite-specific history search and verifying concurrent turn writes.

## 11. Plan deployment readiness around the client's infrastructure

Docker Compose packages the local demo for reviewers. For a real rollout,
start with the client's existing hosting, identity, networking, data services,
and release process. Consider running the existing automated checks in CI,
publishing versioned images to the client's registry, and adding staged
deploys, health checks, and rollback. Plan how secrets, migrations, and
operational ownership fit the client's environment before choosing a platform.

## 12. Evaluate observability for a production deployment

Assess what the current OpenTelemetry instrumentation and OTLP export can
support in the client's environment. Identify what can be reused and what
would need to change to add aggregate latency and error dashboards, alerts,
and visibility into provider retry attempts. Consider how sampling,
retention, and content redaction would fit the client's stack.

## 13. Evaluate production reliability and spending controls

Assess how far the demo's retry and per-turn limits get us toward the
client's availability, traffic, and budget requirements. Determine what
would need to change to enforce rate limits, usage quotas, and spend caps
across instances. Evaluate whether provider failover is warranted and what
would be needed to preserve tool behavior and streaming during a failure.

## 15. Review the idempotent-send contract

Review why clients generate one key per intentional send and reuse it on
retries, including how the API handles an active turn and replays a saved
reply. Compare alternatives such as a client-generated message ID or a
separate status lookup. Consider how each handles ambiguous network failures,
duplicate model calls, and intentional sends with identical text.

## 17. Evaluate experimental Harness compaction for a real client

The MVP uses an experimental Harness feature, pins the dependency, and tests
summary persistence, reload, and cutoff calculation. Capper relies on the
summary marker and output shape to infer the cutoff. Before a real deployment,
review the client's tolerance for experimental dependencies and their
preferred, well-tested infrastructure. Compare retaining the pinned
integration with adopting a supported alternative or owning compaction in
the application. Weigh maintenance, upgrade risk, and operational ownership.

## 18. Revisit background compaction if inline latency matters

Use traces to measure compaction delays against the client's latency goals.
Preparing a summary early could shorten the triggering turn, but costs model
calls for summaries that may never be used. The MVP experiment was removed
because reloaded history never matched the prepared summary. If revisiting
it, tie each prepared summary to a stable message boundary, verify it still
matches before use, and use shared storage across instances where needed.

## 19. Review recovery from provider context-limit rejections

Evaluate a targeted retry after explicit rejection and discuss provider-side
truncation, including how it can discard useful context. Compare these with
the current fail-and-report behavior. Preserve tool-call/result pairs and
avoid replaying actions or duplicating streamed output. Pre-send token
estimation and provider-side truncation are outside MVP scope.

## 20. Preserve preferences the user hasn't explicitly asked to save

Evaluate which preferences get missed after compaction. Consider asking
“Do you want me to remember that?” when a durable preference comes up,
or checking for important unsaved preferences before compaction. Compare
recall improvements with the added latency and interruptions, and keep
the user in control of what becomes a saved guidance note.

- **21. Conflicting guidance notes.** Explore recognizing when a new preference
  may replace a saved one and asking whether to remember it as an update.
  Keep the existing tools and newer-note precedence for the MVP.

## 22. Discuss the history budget and compaction threshold

Explain the MVP defaults: a 20,000-token history budget, a 75% trigger,
and an 8,000-token retained-history target. Compare earlier compaction,
which leaves more headroom but can increase summary calls and compress
details sooner, with later compaction, which retains verbatim history
longer. For a client, use traces and recall evals to tune the budget and
threshold against latency, cost, and answer quality.

## 23. Compare catalog search approaches

Keep literal substring search for the MVP. For a client, compare synonym
expansion, trigram fuzzy matching, embedding-based semantic search, and
hybrid retrieval. Evaluate them against real catalog queries, including
misspellings and differences between customer and catalog wording. Compare
relevance, latency, and operational cost against the existing baseline.

## 24. Compare ways to improve product recommendations

Use a user's purchase history to suggest similar or complementary items.
Compare simple item-type matching, aggregate co-purchase rankings, and
embedding-based similarity. Evaluate real-time retrieval against cached
groups of related products, including how to refresh the groups when the
catalog changes. Compare relevance, latency, and maintenance cost against
the MVP's popularity and purchase-history tools.

- **25. School-level rankings.** Ranking purchases by school is demonstrative
  only. With real purchase data, a small group or an item bought repeatedly
  by one household could expose that household's buying habits. Consider a
  minimum number of distinct buyers per product and a broader fallback.

## 26. Ground product cards in actual lookup results

Treat this as a priority gap beyond the MVP. Explore caching the results of
catalog lookups on the server and giving the model opaque references to those
results. Resolve card requests against references the server issued for this
user and conversation, then revalidate the product against current eligibility
and the avoid list. Choose a lifetime that supports follow-ups such as “show
me the first one again,” and define how the model should recover when a
reference has expired.

## 27. Evaluate semantic matching for avoid-list changes

Compare text matching with product-description embeddings for resolving
natural-language references when adding or removing avoided products.
Evaluate matching within the relevant catalog or the user's saved avoid
entries, and use semantic results as candidates to clarify when ambiguous.

## 28. Evaluate persistent pagination cursors

Keep current pagination for the MVP. Consider storing the query and next
cursor together in user- and conversation-scoped server state so a follow-up
can resume after compaction clears tool results. Compare that with the
current context-only cursor. Weigh continuity against state lifetime,
stale results after catalog changes, and ambiguity when several searches
are active. Consider reusing the lookup state proposed in item 26.

## 29. Revisit oversized tool results if needed

Keep the MVP's size limit and narrow-and-retry behavior. If a future tool
needs to return a large result in full, compare native pagination with
temporarily storing the result server-side and retrieving bounded slices.
Weigh access scoping, expiration, storage cost, and latency.

## 30. Evaluate queryable message parts

Keep the ordered JSON transcript for MVP replay. If cross-conversation
queries become important, consider an indexed projection of card impressions
keyed by message, product, and part position. Write it with the transcript
and backfill it from saved messages if historical reporting is needed.
For broader queries across several part types, compare a normalized
message-parts table with explicit ordering. Weigh query performance against
migration, replay, and write complexity.

## 31. Define confirmation for future action tools

Revisit confirmation when Capper gains tools that change account or business
state, such as applying a referral code. Compare requiring confirmation for
all such changes with rules based on impact and reversibility. Consider
showing the exact pending action, rechecking authorization and eligibility at
execution, and handling expiration and retries without duplicate side effects.
Weigh accidental actions against the friction of an extra step.

## 32. Improve ingestion and publishing of canonical business documents

Keep the manifest and repository workflow for MVP. For a client, define
which sources are authoritative and validate new versions before publishing.
Consider redacting sensitive material, excluding irrelevant or unapproved
sections, and keeping uploaded reference material separate from trusted model
instructions. Evaluate an LLM judge to flag conflicts, unsupported changes,
and redaction misses for human review. Consider an admin portal for targeted
edits with previews, approval permissions, version history, and rollback.

- **33. Resolve conflicting or missing sources.** The MVP assumes the
  curated documents are cohesive after applying the documented precedence.
  Improve ingestion by flagging contradictions and missing references for
  the client to review, then record which source governs each disputed rule.
- **34. Retrieve passages from longer documents.** Today, the manifest
  selects approved files. Capper loads short documents whole and can fetch a
  specific on-demand document by name. If the client's material grows longer
  or more complex, evaluate retrieval-augmented generation (RAG) behind the
  document tool. Chunk approved sources, retrieve relevant passages, retain
  source and version, and keep internal-only material outside the retrievable
  collection. Compare passage retrieval with whole-document loading.

## 35. Evaluate multilingual support

The MVP replies in English. For a client, compare answering in the user's
language from canonical English sources with publishing approved translations
and localizing conversation search. Consider the cost of keeping translations
in sync, search quality across languages, and evals that check whether
translated answers preserve business rules and policy meaning.

## 36. Consider a separate user preferences model

The MVP can store the time zone directly on the user record. As settings
grow, consider moving time zone and similar UX preferences into a separate
model or using the client's existing preferences system. Decide which
settings belong to the account and which should follow the current device.

## 37. Evaluate deep history cleanup and targeted redaction

The MVP deletes saved guidance and avoid-list records directly. For a client,
distinguish updating preferences, suppressing a detail from future model
context, hiding it from the transcript, and deleting or redacting it from
storage. Consider how a change would propagate to the transcript, search
index, model history, and compaction summaries. Tie this to items 20 and 21
so preference updates and privacy requests have clear, distinct behavior.

## 38. Refresh the OWASP review before the presentation

Check the latest published OWASP Top 10 for LLM Applications against the
2025 edition used in the prior review. Map relevant guidance to Capper's
actual controls and prepare to explain any gaps and their priority for a
real deployment.

## 39. Review audience scope for the presentation

Discuss how a client would define the supported ages and regions. Ask what
account-level controls already exist and consider what Capper would need to
do if children use a parent's account or if the service expands outside
the United States.

## 40a. Explain why Stop preserves the partial reply

Review the choice to keep the content already streamed to the user and mark
the turn as stopped. Be ready to demonstrate how the transcript replays it.

## 40b. Explain why chat and compaction use separate models

Review what the main model handles versus what the cheaper summarizer does.
Discuss the cost, latency, and quality trade-offs of using two models.

## 40c. Explain the limits of saved guidance

Review how saved guidance personalizes replies, how the server enforces
product exclusions through the avoid list, and why remembering an allergy
does not establish that a product is safe.

## 41. Explain eval coverage and where to extend it

Keep MVP evals lightweight. Clean up the existing evals and add cases during
MVP cleanup only when they cover behavior essential to the demo. Prepare
talking points that distinguish deterministic application checks, retrieval
quality, live-model tool behavior, and answer quality evaluated by a human
or a calibrated model judge. Use recall after compaction, a relevant product
beyond the first page, and avoid-list handling as examples of where to extend
coverage based on risk.

## 42. Consider a more robust user profile system

The MVP personalizes replies using conversation history, summaries, explicitly
saved guidance, and purchase lookups. It doesn't automatically build an
interest profile or learn from reactions to recommendations. Consider a more
robust profile system that maintains interests and preferences over time,
using conversation, purchases, and recommendation feedback where appropriate.
Explore how users could review, correct, and remove inferred preferences,
and compare the added value with the current explicit-memory approach.

r# 43.
might be a dupe, but 3. **Two records of the conversation.**
   - *Over:* one table in the framework's format.
   - *Why:* the transcript is what the user saw and never changes; the model
     history is what the model works from, and clearing and compaction change
     only what's sent from it. A framework upgrade can't break old
     transcripts. Deduping would also have cost extra database writes with the
     way we use them.
   - *Cost:* Duplicate data, written in one transaction.

