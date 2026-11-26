# MVP Plan

We design (full design documentation) and build (a working MVP) one app:
Capper, Dockerized. Everything in this plan is designed **and** built. Anything
not in it is in `future-considerations.md`. Settled decisions live in
`decision-log.md`. How each item is built, and how the build is checked, is
in `mvp-technical-design-document.md`. Formerly `open-tasks.md`. Topics
waiting to be sorted are in the discussion list below.

**Two buckets only (D-078):** an item is either kept here (built) or listed in
`future-considerations.md`. There is no "design only" tier. Sam sorted every
item on 2026-11-17; the punted ones (#24 → D-088, #31 → D-086, #33, #35–39, #41–43, #48) are listed
under "Punted from the MVP" in `future-considerations.md`. Item numbers are
kept stable so references elsewhere still resolve.

**Origin** is where an item sat before the 2026-11-17 merge: **MVP** (already
in the build), **Plan** (previously designed only; now built), **Doc** (design
documentation, deliverable #1), **New** (added 2026-11-17).

## Interviewer answers (relayed by Sam, 2026-11-16)

1. **Provider / API key:** Sam provides an API key and we build against it
   (provider: OpenAI, D-047).
2. **Deployment:** punt; build the POC only. The service is Dockerized (#1);
   deploying it is a future consideration.
3. **Schema changes:** assume they're allowed.
4. **Scope of product behaviors/documents:** support what's clear from the
   brief and the interaction examples in the UI design PDF (as behaviors
   built from generic capabilities; their subject matter is illustration,
   D-057). No extra
   documents (terms of service, privacy policy, help center) for now.

## The MVP

| # | Item | Origin | Needs | Decisions | Why kept / notes |
|---|---|---|---|---|---|
| 1 | **Dockerize the service** | New | 2 | D-092, D-094 | Sam's decision. A fully Dockerized product (D-094): data in a Docker volume; an `init` service bootstraps idempotently (keys, supplied database, migrations, seed, content); the service is health-checked. First run is `cp .env.example .env`, set two values, `docker compose up`. Specs, checks and evals run in a `dev` container. |
| 2 | Environment and tooling: uv, Python 3.14, settings, app factory, pyright strict, Alembic, `pip-audit` | MVP |  | D-072, D-077, D-094 | Built inside the Docker images (D-094): uv with locked dependencies and dependency groups, Python 3.14, pydantic-settings from the environment Compose passes, strict pyright, Alembic, `pip-audit`. Starting limits are TDD defaults (Appendix A #18). |
| 3 | Content authoring: scope charter, persona and voice, greeting, do-no-harm core and policies, product knowledge, compaction summary template with required headings (D-091) | MVP |  | D-049, D-060, D-069, D-070, D-077, D-091 | brief: aligned with purpose; referral process; mockup hand-off |
| 4 | Ingestion and the content table, with hand-curated referral text | MVP | 2, 3 | D-050, D-053, D-055, D-090 | brief: knowledge base changes; referral process Each turn uses one content snapshot; published text is immutable; publishing clears the previous rows' `active` flag in the same transaction (D-090). |
| 5 | Schema migration and seed data | MVP | 2 | D-071, D-090, D-092 | `summaries` watermark is `covers_through_model_message_id` (D-090). The supplied and seeded catalog is the participating catalog, so no participation field (D-090). The legacy `Conversation_History` table is dropped and there is no control user (Sam, D-092). |
| 6 | Auth: token verification and demo sign-in | MVP | 2, 5 | D-020, D-092 | Don't over-engineer or recreate logic the brief hands us (the existing auth API). Login is the auth API's job; the brief's API is hypothetical, so the demo page lists users and clicking one creates a session (a normal token, verified like any other). This is the one exception to no test modes (Sam, D-092). No simulated login, stubbed API or separate service. |
| 7 | Product search and product cards | MVP | 5 | D-056, D-058 | brief: personalized product recommendations; mockup cards |
| 8 | Promotions and promotion cards | MVP | 5, 7 | D-058 | mockup: Bonus Caps cards |
| 9 | Referral code lookup | MVP | 5, 6 | D-058 | mockup: personal referral code |
| 10 | Purchase history lookup | MVP | 5, 6 | D-059 | brief: user context |
| 11 | Popular-products fallback | MVP | 5, 10 | D-070, D-090 | POC: easy once seeds exist; an empty list is acceptable. Aggregate rankings only; avoided products excluded; basis "at your school" or "overall" (D-090). |
| 12 | History search (SQLite full-text) | MVP | 5, 16 | D-074, D-090 | A bounded top-5 relevance lookup over message text, exempt from the cursor contract; cards aren't indexed (D-090). |
| 13 | Do-no-harm policies loaded on demand (`read_document`) | MVP | 3, 4 | D-049, D-058, D-090 | mockup: health and safety awareness (R-07). `read_document` reads the turn's content snapshot (D-090). |
| 14 | Avoid list (filters product results) | MVP | 5, 7 | D-051, D-068 | — |
| 15 | Guidance notes (caps, expiry, newer supersedes older) | MVP | 5 | D-051, D-067, D-068 | — |
| 16 | Conversation API: greeting, history, send (NDJSON stream with text and cards), idempotency, one active turn | MVP | 6, 17 | D-063, D-056, D-090, D-092 | brief: API that creates and maintains multi-turn conversations; mockup greeting Duplicate sends: same key and text → 409 while running, 200 replay of the stored turn once ended; same key, different text → 422 (D-090). The turn and user message are committed before generation; turns left `in_progress` at startup are marked `error` (D-090). Errors before streaming are HTTP statuses; after, one terminal `error` event (D-090). One outcome table governs stream, saved state and replay; the user prompt is stored at turn start; the turn commits before the terminal event (D-092). |
| 17 | Agent and context builder (instructions, per-user context, history view) | MVP | 3, 4, 5 | D-044, D-072, D-092 | brief: LLM integration, prompt engineering, context management Pydantic AI 2.69: history processing is the `ProcessHistory` capability (D-087). Account and turn context are request-only: injected after compaction, never persisted or summarized (D-092). |
| 18 | Stop endpoint; a disconnect doesn't cancel (background generation) | MVP | 16 | D-046, D-090 | mockup: stop button Stop is bound to the turn: `POST /v1/conversation/turns/{turn_id}/stop` (D-090). |
| 19 | Provider failures: retry before the first token, one generic error event | MVP | 16 | D-061, D-090 | Bounded SDK retries of individual model requests; never an automatic replay of the agent turn (D-090). |
| 20 | User feedback endpoint (thumbs up/down, comment) | MVP | 16 | D-076 | — |
| 21 | Context budget: the Harness triggers check the size before every model call; `ReportContextUsage` puts budget usage on the trace | MVP | 17 | D-064, D-089 | brief: context management |
| 22 | Tool-result clearing via the Harness (current turn whole, last 5 kept) | MVP | 17 | D-065, D-090 | Future note: extensibility and maintainability of the Harness. Part of the #23 tiers. Configuration (D-087): `keep_pairs` = per-turn tool-call limit + 5; tool calls stay visible; `min_clear_tokens` set. Protects the active turn and at least the five most recent past-turn results; re-running a cleared tool is a fresh read (D-090). |
| 23 | Compaction on the Harness: `ClearToolResults` then `SummarizingCompaction` on the compaction model, our structured prompt, token-based retention; we persist the summary and watermark | MVP | 21 | D-043, D-089, D-090, D-091, D-092 | brief: context management, memory limitations. No sliding-window fallback: if compaction fails, the turn fails with the generic error. No background start (D-096). Watermark at the model-message level; reload = latest summary + messages after it; 75% trigger enforced, ~40% a tuning target via `keep_tokens` (D-090). Summary format (D-091): the Harness summarizer with our fixed template; required headings checked before saving, failing visibly if missing; a Pydantic schema only if app code ever reads summary fields. Watermark computed by position; heading check is a summarizer output validator; per-user `conversation_id`; no tiered `skip_on` (D-092). |
| 25 | Prompt caching and OpenAI request settings (per-user cache key, `store: false`, current-turn reasoning) | MVP | 17 | D-047, D-050, D-052 | `openai_send_reasoning_ids` off; encrypted reasoning round-trips with `store: false` (D-087). |
| 27 | Demo chat page (thin, escapes HTML, served by the app) | MVP | 16 | D-019, D-077, D-092 | Starts with the user list sign-in (D-092). |
| 28 | Specs: deterministic parts, context building, cross-account, stop/continue | MVP | 7–23, 25, 32, 34, 40 | D-062, D-090 | brief: unit and/or integration tests. Includes a deterministic compaction-persistence spec: transcript untouched, reload yields the summary plus exactly the remaining messages, tool pairs intact (D-090). |
| 29 | Tool-call eval (`read_document`) | MVP | 13 | D-062 | Future note: talking points for a more robust eval system. |
| 30 | LLM-judge answer-quality eval (commented out) | MVP | 16 | D-062, D-090 | Sam's request (D-062). An example, labeled as such, not an executed quality check (D-090). |
| 32 | One logging and tracing solution: OpenTelemetry traces to a local viewer container (message content off; step detail and per-turn summary on spans; absorbs former #26) | Plan | 1, 16 | D-075, D-079 | D-079. |
| 34 | Cursor paging on list tools | Plan | 7, 16 | D-064, D-080, D-092 | D-080 (REST list paging punted). **Design note, tool result size contract:** (1) every list tool has a default and a maximum page size and returns `items`, `total_count`, `next_cursor`, and the model states how many are shown out of the total when a list is partial (the wording is checked by the eval, not a spec, D-092); (2) counts and "how many / which ones" questions use query filters, not paging through everything (D-043); (3) every tool result has a configurable size cap; a result that hits it returns an explicit "result too large, narrow the request" to the model, never a silent cut (D-088); (4) tool descriptions tell the model about totals and cursors; (5) specs check that a partial list always states its total and an oversized result is never silently truncated. Deterministic keyset order per list; `get_popular_products` follows the contract (D-092). |
| 40 | Do-no-harm safety net: a check agent awaited before the first model request | Plan | 13 | D-049, D-090 | A simple POC, not a robust, harshly graded system. Ordering (D-090): runs concurrently with context building and is awaited before the first model request (default 2 s timeout); a flagged policy from the turn's content snapshot is added to the per-user context; on failure or timeout the turn proceeds without it (fail open) and the trace records it. Policy areas are the on-demand policy documents in content (D-057). |
| 44 | API contract spec | Doc | 16 | D-063, D-076, D-090 | brief: API contract |
| 45 | Diagrams for engineer onboarding | Doc | 17 | D-072, D-050, D-043 | brief: diagrams |
| 46 | Mobile integration notes | Doc | 16 | D-063, D-090 | brief: mobile integration |
| 47 | Privacy considerations | Doc |  | D-066, D-052, D-051 | brief: privacy considerations |
| 49 | Final summary (from `future-considerations.md`) | Doc |  |  | brief: point of view, priorities, evolution |

## Roadmap to submission (Sam, 2026-11-17)

The high-level steps from here, in order. Each finishes before the next starts.

1. **Sort the discussion list** (above), one item at a time: an MVP to-do, a
   future consideration (`future-considerations.md`), or dropped as settled or
   irrelevant.
2. **Adversarial agentic code review.** Sam provides the review; we work
   through and normalize its findings.
3. **Behavior test against the brief.** Sam tests the running app against
   `challenge-criteria.md`.
4. **Manual code and documentation review** by Sam.
5. **Presentation preparation:**
   1. the README;
   2. a feature list: what the brief asked for, and what we added (such as
      the do-no-harm safety check);
   3. data flow diagrams;
   4. the final presentation.
6. **Wrap-up:** a final workspace cleanup, a clean-install test, then package
   and submit.

## Discussion list (2026-11-17): to sort into MVP or future considerations

One numbered list for Sam to sort, each item into keep (build or accept in the
MVP) or punt (`future-considerations.md`) (D-078). It holds:
- **1–17:** where the build diverged from the reviewed design. The review's
  design summaries (`second-agent/interview-review.md`) are merged with the
  build log's "Deviations from the TDD" and "Known limitations".
- **18–33:** the concerns Sam marked in that review's "Findings from the
  walkthrough".

The suggested bucket is Claude's; Sam decides.

| # | Topic | From | What it is | Suggested bucket |
|---|---|---|---|---|
| 1 | Docker setup reworked | Review 3; D-094 | Data in a named volume, an idempotent `init` service, `/healthz` (API-15), a `dev` container for checks. The reviewed design was the explicit seven-step sequence. TDD §2 rewritten | MVP: done, decided by Sam |
| 2 | Everything ships in the image | Review 25; D-094 item 6 | Content, product images (now packaged SVGs served at `/images/products/…`, replacing an external placeholder service) and the supplied database are all in the image. TDD updated | MVP: done, decided by Sam |
| 3 | Safety check tuned and measured | Review 24, 29 | No reasoning, native structured output and a 200-token cap: median 1.71 s → about 1.0 s, no timeouts. Time to first token now counts from turn start; the turn span records `capper.safety_outcome` and `capper.safety_wait_ms`. TDD updated | MVP: done |
| 4 | Interrupted tool calls closed by the framework | Review 27, 28; API-14 | Pydantic AI closes an unanswered tool call with an `interrupted` result when history is next sent, so Capper writes no synthetic "not run" result of its own. Proven by a spec that stops a turn mid-tool | MVP: done, decided (D-095); API-14 updated |
| 5 | Request-limit backstop is the tool limit + 4 | Review 11, 20; TOOL-4 | Not + 2: the summarizer's requests count against the same run limit, so + 2 could end a turn that compacted | MVP: accept, update TOOL-4 |
| 6 | The budget trigger counts the whole request | Review 20; CMP-1 | The Harness anchors on the provider's reported input tokens, which include instructions, tools and the request-only blocks. Those blocks are still never stored or summarized | MVP: accept, reword CMP-1 |
| 7 | Settings added or given defaults | §13 | `git_sha` added (`compaction_background_start` was added, then removed by D-096); JWT key paths, issuer and audience given defaults (the bootstrap creates the keys) | MVP: accept (key paths already in §13) |
| 8 | Deps carry services; a tool guard capability | Review 2, 11; AGT-6, AGT-7 | Tools get services rather than the session factory and settings. TOOL-3's adapter is a capability (`ToolGuard`) added to AGT-7's list | MVP: accept, update AGT-6 and AGT-7 |
| 9 | The summary template has a fourth heading | Review 22; CNT-1, D-091 | "What happened" added, so a summary keeps results. Required headings are read from the template | MVP: accept, update CNT-1 |
| 10 | Flagged policy reaches the model `<system>`-framed | Review 18, 24; CTX-1 step 5 | Pydantic AI renders a system part that sits mid-conversation as operator-voice text in the user turn, its documented convention | MVP: accept, note in CTX-1 |
| 11 | Background compaction is never used | Review 22; known limitation | A spec showed every summary prepared in the background is discarded (the stored prompt never matches the run's stamped copy); compaction ran inline anyway | MVP: done, background start removed (D-096); a working head start is a future consideration |
| 12 | SDK retries aren't on the trace | Review 29; OBS-3 | The OpenAI SDK retries before a request starts, invisibly to Capper. Summarizer retries do show | Future considerations |
| 13 | Ingestion strips authoring notes | Review 9; ING-1 | HTML comments in content sources (who authored or curated it) are removed before hashing and publishing, so they never reach the model | MVP: accept, note in ING-1 |
| 14 | History search ORs the quoted terms | Review 16; D-074 | Any term can match, ranked by bm25. With AND, a natural-language query rarely matched | MVP: accept, note in §8.2 |
| 15 | Clearing's trigger | Review 21; CMP-3 | The TDD set none and the Harness requires one; it's the compaction trigger (75% of the budget), so clearing runs before any summary | MVP: accept, note in CMP-3 |
| 16 | Dependency-injection seams in `create_app` | Review 30; D-007 | Optional models, safety checker, tracer provider and clock, for specs and evals. EVAL-1 composes the turn without the safety check this way. No production switch | MVP: accept |
| 17 | Spec set changed | Review 30; §16 | TEST-14 dropped with the control user (D-092). Added: bootstrap idempotency, health, product images, OpenAPI drift (with an export script), safety timing and no content in spans. 102 specs | MVP: accept, update §16 |
| 18 | Idempotency-Key assumption | Walkthrough topic 26 | The API assumes the client generates one key per logical send and reuses it across retries. Sam wants to think it through before presenting | Future considerations (note) |
| 19 | SQLite to a managed database | Walkthrough topic 3 | For a real client, move to their managed database or PostgreSQL early, especially for multiple instances or concurrent writes. Discuss the timing before presenting | Future considerations |
| 20 | Content authoring and publishing | Walkthrough topic 9 | Admin editing (an upload-triggered LLM-assisted ingestion, or an admin portal), staged CI/CD-style publishing with validation, an LLM reviewer for inconsistencies. Risk: always-loaded content is instructions, so who can edit, approve and activate it matters | Future considerations |
| 21 | Message parts as a JSON array | Walkthrough topic 8 | Cross-conversation queries by part type (for example, counting a product's cards) must expand every array. Sam wants an alternative developed | Future considerations |
| 22 | Persist prepared summaries across instances | Walkthrough topic 22 | Flush a prepared Harness summary and its cutoff to shared storage at turn end, so another instance can apply it. Related to 11. Sam will research the Harness integration | Future considerations (Sam marked it outside the MVP) |
| 23 | Capture the exact summary boundary | Walkthrough topics 22–23; CMP-7 | Carry an explicit cutoff from the Harness instead of inferring it from the result's length. The pinned Harness's `compact()` returns only the new message list (`[summary, *kept]`), with no boundary, so this needs a Harness change or a wrapper | Discuss: MVP or future |
| 24 | Model-call provenance on the trace | Walkthrough topics 18, 29, 30 | Per model call: model, content version, summary ID and cutoff, tools called, whether compaction ran. Also opt-in capture of the exact outbound request and response for seeded demo or eval runs only, to diagnose eval failures. No conversation text in routine logs | Discuss: MVP or future |
| 25 | Retrieve history by date or position | Walkthrough topic 16 | Date-range filters, and fetching a bounded batch of transcript messages around a point, so Capper can look back without a keyword match. Sam asked to review it for the MVP | Discuss: MVP (Sam's flag) |
| 26 | Avoid-list placement | Walkthrough topic 17; D-051, D-058 | Test whether naming avoided products in account context makes them more likely to appear, against enforcing only in queries and cards and showing the list only when asked. Keep a way to identify which product to remove | Future considerations (an eval case) |
| 27 | Cards only for products shown this turn | Walkthrough topic 15 | A turn-local set of IDs that lookups returned; `show_products` refuses an ID outside it, which catches a hallucinated but real ID | Future considerations (Sam marked it outside the MVP) |
| 28 | Resume "show me more" | Walkthrough topic 14 | Persist the original query and its cursor as app state, so paging resumes after the tool result was cleared or compacted. The MVP paging stays | Future considerations |
| 29 | School-based popularity privacy | Walkthrough topic 13 | The school ranking is an MVP placeholder; review its privacy for schools with few users. Production needs the client's business sign-off | Future considerations |
| 30 | Semantic catalog search | Walkthrough topic 12 | Embeddings for names and descriptions behind the same `search_products` interface, with the avoid list enforced in code. Compare quality with literal search first | Future considerations |
| 31 | Context-limit handling | Walkthrough topic 20; CMP-6 | Estimate the request before sending and trim, or catch a context-limit rejection and retry smaller (preserving tool pairs, no replayed actions, no duplicate stream). **Note:** D-092 records Sam's decision that we never estimate request size before sending; the reactive retry is the open part | Future considerations |
| 32 | Present the safety routing | Walkthrough topic 24 | Presentation follow-up: the lighter model picks policies while context is assembled; on timeout, the core instructions and on-demand lookup still apply. Item 3 has the measured numbers | Future considerations (presentation) |
| 33 | Debugging a turn from its trace | Walkthrough topic 29 | Presentation prep: reading a turn's trace, model and tool spans, token counts (input, output, cached), time to first token, retries and compaction events | Future considerations (presentation) |

## Housekeeping

| # | Task | Status |
|---|---|---|
| H1 | Append every turn to `conversation-log.md` | ongoing |
| H2 | Remind Sam of commit checkpoints | ongoing |

## Where earlier IDs went

The original Q1–Q8 (2026-11-16), W1–W14, T-tasks and the sort questions
Q1–Q8 (2026-11-17) are all settled; `decision-log.md` maps each to its
decision. The former build tasks B0–B10 are items 2–30; the former write-ups
T6, T10, T11, T12 and H3 are items 44–47 and 49 (T9 was punted with #48).

---

# Capper MVP — Technical Design Document

> **Historical document only.** This document was used to design the MVP and
> is no longer a canonical source of truth for the project.

The authoritative implementation plan for the MVP. After the build, the work is
checked against this document for drift, cut corners, invented behavior and
scope creep. Code quality is checked against `code-standards.md`.

## 0. How to use this document

1. **Sources of truth.** `mvp-plan.md` says *what* ships; `decision-log.md`
   says *what was decided and why*; this document says *how it is built*,
   precisely enough to check. When this document and a decision disagree,
   the decision wins and this document is the bug.
2. **Requirement IDs.** Every buildable requirement has an ID (`ENV-3`,
   `API-7`, ...). Each cites the decisions it comes from. The build is
   complete when every requirement's **Check** passes.
3. **TDD defaults.** Where the decisions leave a detail open (a number, a
   name, a file path), this document picks one and marks it **(TDD
   default)**. All of them are listed in Appendix A so they can be reviewed
   and changed deliberately. Anything that is neither cited nor marked is a
   defect in this document.
4. **Scope.** Only the items kept in `mvp-plan.md` are built. Everything else
   is in `future-considerations.md` (Appendix C lists what must **not** be
   built). Adding behavior not described here is scope creep, even if it
   seems helpful.
5. **Build-time verifications** (Appendix B). Library wiring that can only be
   confirmed while building is resolved during the build and recorded against
   the affected requirement. Only a failure that would force a change to
   agreed behavior stops the build and is raised with Sam.
6. **Worked sequences.** §2.1 (clean checkout to first turn) and §10.1
   (compaction to persisted reload) are the reference flows where several
   components meet; each is also a check.
7. **Requirements, defaults and examples.** A build directive is a
   requirement here that traces to a current decision, or a marked TDD
   default. An example (a quoted user message, a sample product or health
   detail, a walkthrough) illustrates a requirement or is a test fixture; it
   is never scope on its own. Only wording a decision fixes is quoted as
   required wording (D-093).

## 1. What we're building

Capper is a chat assistant service for the Carton Caps mobile app: a FastAPI
service that streams conversations as NDJSON, powered by a Pydantic AI agent
on OpenAI, with the context-engineering features that are the focus area
(D-002): a context budget, tool-result clearing, compaction with persisted
summaries, saved user guidance, and history search. It runs in Docker next to
a local trace viewer, with a thin demo web page. One app; two buckets
(D-078).

**Generic capabilities, not use-case features** (D-057, code standard 7.3):
tools look up and modify data, the agent builds responses, and the agent saves
relevant user data. Domain subject matter (whatever the catalog or the
mockups happen to show) appears only in content and in test and eval cases,
never in tools, schemas or code paths.

## 2. Environment and runtime (mvp-plan #1, #2; D-094)

Capper is a fully Dockerized product: it runs only in Docker, and its data
lives in a Docker volume (D-094).

- **ENV-1 Python and packaging.** Python 3.14; uv manages dependencies and the
  lockfile (`uv.lock`) inside the image build; `pyproject.toml` builds one
  package with three modules under `src/` (`capper`, `content_bundle`,
  `ingestion`) using hatchling (D-072, code standard 8.1). *Check:* the image
  builds with `uv sync --locked`.
- **ENV-2 Runtime dependencies** (direct), each listed with its reason in the
  README (code standard 8.2): `fastapi`, `uvicorn`, `pydantic-ai-slim[openai]`,
  `pydantic-ai-harness` (pinned exactly, D-064), `pydantic-settings`,
  `sqlalchemy[asyncio]`, `aiosqlite`, `alembic`, `pyjwt[crypto]`,
  `opentelemetry-sdk` and `opentelemetry-exporter-otlp-proto-http` (D-079).
  *Check:* every direct runtime dependency in `pyproject.toml` is on this list
  or justified in the README.
- **ENV-3 Dependency groups.** `dev`: `pytest`, `pytest-asyncio`, `httpx`,
  `ruff`, `pyright`, `pip-audit` (D-072, D-077). `evals`: `pydantic-evals`
  (D-062). No `ingestion` group is needed, because MVP sources are Markdown
  (ING-1) **(TDD default)**. *Check:* evals and dev tools are absent from the
  runtime image.
- **ENV-4 Tooling.** `ruff format`, `ruff check`, `pyright` in strict mode,
  `pytest` and `pip-audit` all pass, run in the `dev` container (code
  standards 8.7, D-077, D-094). *Check:* each command exits 0.
- **ENV-5 Configuration.** One `Settings` class (pydantic-settings) read once
  in the composition root; `CAPPER_*` environment variables (from `.env`
  through Compose) override defaults; `OPENAI_API_KEY` is read without the
  prefix (code standard 7.6). `.env.example` is committed; `.env` is ignored.
  The full settings list is in §13. *Check:* no module other than the
  composition root reads settings.
- **ENV-6 Dockerfile.** Multi-stage, on the official Python 3.14 slim image
  **(TDD default)**:
  1. a build stage installs the locked runtime dependencies with uv;
  2. the `runtime` target holds everything the MVP uses, never fetched or
     mounted at runtime (D-094): the virtual environment (with the package's
     demo page and product images), `scripts/`, `alembic/`, `alembic.ini`,
     `content/` and the supplied database fixture. It runs as a non-root
     user, owns `/app/data` (the volume's mount point), and exposes port 8000;
  3. the `dev` target adds the `dev` and `evals` groups, `tests/` and `evals/`.

  *Check:* the runtime image contains no dev or eval packages.
- **ENV-7 Docker Compose** (`compose.yaml`) **(TDD default names)**:
  1. `init`: the runtime image running the bootstrap (ENV-9) once, with the
     `capper-data` volume at `/app/data`;
  2. `capper`: the service, started only after `init` completes successfully,
     with the same volume, `env_file: .env`, port 8000, and a health check on
     `GET /healthz` (API-15);
  3. `traces`: Jaeger all-in-one (OTLP HTTP on 4318, UI on 16686) (D-079);
  4. `dev` (profile `dev`): the `dev` image for specs, checks and evals, with
     the same volume and `.env`.

  Image tags are pinned to exact versions.
- **ENV-8 Startup.** The `capper` process only serves. At startup it marks any
  turn still `in_progress` as `error` (D-090, code standard 6.6). Migrations
  and data bootstrap belong to `init` (D-094).
- **ENV-9 Bootstrap** (`python -m scripts.bootstrap`, run by `init`;
  idempotent, safe on every `up`) (code standard 1.3, D-094), in order:
  1. create the dev RSA key pair under `/app/data/keys/` if missing;
  2. copy the supplied fixture to `/app/data/capper.db` if missing;
  3. `alembic upgrade head`;
  4. seed (§5.5);
  5. ingest the content shipped in the image (§6), publishing only changes.

  Tests mint their own tokens in fixtures (D-020). *Check:* `scripts` is not
  importable from `capper` routes or services; a second `up` changes nothing.
- **ENV-10 README** documents the first run, everyday Compose commands (start,
  stop, reset, rebuild, logs), running specs, checks and evals in the `dev`
  container, the layout, configuration, and every dependency with its reason
  (D-085, code standard 8.2).

### 2.1 Worked sequence: clean clone to first successful turn

The reference first run; also the Docker acceptance check (ENV-11).

1. `cp .env.example .env`, and set `OPENAI_API_KEY` and
   `CAPPER_CACHE_KEY_SECRET`.
2. `docker compose up --build`: builds the image; `init` creates the keys,
   copies the supplied database, migrates, seeds and ingests; then `capper`
   starts (ENV-8) next to the trace viewer, and turns healthy.
3. Open `http://localhost:8000/`, pick a user from the list (AUTH-5), send a
   message: the reply streams and the turn's trace appears at
   `http://localhost:16686`.

Reset to a clean state with `docker compose down -v`.

- **ENV-11** *Check:* the sequence above, run on a clean clone, ends with a
  streamed reply and a visible trace, with no manual step outside it
  (D-085, D-094).

## 3. Code structure (D-072, code standards 7.4–7.7)

```
src/capper/
  app.py          composition root: settings, engine, session factory, agent, routes, lifespan
  config.py       Settings
  db.py           declarative Base, async engine and session factory
  errors.py       domain exceptions (mapped to HTTP in one place, API-13)
  telemetry.py    OpenTelemetry setup (OBS-1)
  auth/           token verification → current user (§7)
  accounts/       users, schools, referral codes: models, repository, service
  catalog/        products, promotions, purchases, popularity: models, repository, service
  memory/         guidance notes, avoid list: models, repository, service
  conversation/   api.py, schemas.py, models.py, repository.py, service.py,
                  streaming.py (agent events → NDJSON), stop.py (turn → cancellation token)
  context/        builder.py (pure assembly), inject.py (request-only context capability, CTX-2),
                  compaction.py (Harness wiring + persistence), summary.py (template headings check)
  agent/          agent.py (definition, model settings), deps.py (CapperDeps),
                  tools/ (thin adapters: lookup, display, memory, documents), safety.py
  demo/           static demo page (§12.4); api.py: the demo user list and session routes (AUTH-5)
  health/         GET /healthz (API-15)
src/content_bundle/  the content table model and its read/write functions (shared contract)
src/ingestion/       manifest reading, Markdown loading, publishing
scripts/        bootstrap.py (the init service's entry point), seed.py
content/        manifest.toml, source/*.md (authored and curated content)
alembic/        migrations
tests/          mirrors src/
evals/          tool_call_eval.py, answer_quality_eval.py (commented out)
compose.yaml, Dockerfile, .env.example, README.md
```

- **STR-1** Every domain package has the same shape (`models.py`,
  `repository.py`, `service.py`, plus `api.py` / `schemas.py` where it has
  routes) (code standard 7.4).
- **STR-2** Routes do HTTP only; services hold use cases; repositories hold
  queries scoped by `user_id`; tools are thin adapters over services; no
  FastAPI or Pydantic AI types in services or repositories (code standard
  7.5).
- **STR-3** Budget math, context assembly, summary heading checks and card
  building are pure functions (code standard 7.7).
- **STR-4** `capper` never imports `ingestion`, and `ingestion` never imports
  `capper`; both use `content_bundle` (D-032, code standard 7.1).
- **STR-5** No provider or model names outside `config.py` and
  `agent/agent.py` (D-033, code standard 7.2).

## 4. The agent (mvp-plan #17, #25)

- **AGT-1 Framework.** One Pydantic AI `Agent` with `deps_type=CapperDeps`
  and text output; tools registered as in §8 (D-044, D-056).
- **AGT-2 Model.** Chat model from settings, default `openai:gpt-6.1-terra`
  (Responses API, selected by the model string) (D-047, D-087).
- **AGT-3 Model settings** (D-047, D-050, D-052, D-087):
  `openai_reasoning_context='current_turn'`, `openai_store=False`,
  `openai_send_reasoning_ids=False`, caching on (Pydantic AI `cache=True`,
  implicit, 30-minute default), `openai_prompt_cache_key` = the user's opaque
  key (AGT-5), `max_tokens` = `max_output_tokens`. No
  `openai_previous_response_id`, no `openai_conversation_id`, no OpenAI
  server-side compaction (D-047). *Check:* a spec asserts these settings on
  the built request.
- **AGT-4 Output retries** = `output_retries` (1) (D-043, D-064).
- **AGT-5 Opaque user key.** HMAC-SHA256 of the user ID with
  `cache_key_secret`, hex-encoded **(TDD default for the derivation)**; used
  as the prompt cache key and as the Pydantic AI `conversation_id` for the
  user's runs (D-050, D-052). *Check:* the cache key and conversation ID are the
  opaque key; the app never puts the internal user ID into model context.
- **AGT-6 CapperDeps** carries: `user_id`, `turn_id`, the session factory,
  settings, a clock, the turn's content snapshot (§6.4), the opaque key, the
  per-turn tool-call counter, and the safety-check result (D-044, D-072,
  D-090).
- **AGT-7 Capabilities, in order** (D-079, D-087, D-089): `Instrumentation`
  (content capture off); `ClearToolResults`; the compaction capability
  (§10); `ReportContextUsage`; then the request-only context injector (CTX-2),
  last, so it applies to the compacted request and never enters run history
  (the Harness's documented placement for request-only injectors).
- **AGT-8 Provider failures** (D-061, D-090): SDK-level bounded retries of
  individual model requests before that request's first token; connect
  timeout `model_connect_timeout_seconds` (5 s **(TDD default)**), turn
  timeout `turn_timeout_seconds` (60 s **(TDD default)**); the agent turn is
  never replayed automatically. Any failure after streaming starts is one
  terminal `error` event (API-9).

## 5. Data model (mvp-plan #5; D-071, D-074, D-076, D-090)

All new tables are snake_case; the provided tables keep their names
(D-071). Timestamps are UTC (D-060). Every query on user-owned rows filters
by `user_id` in the repository (code standard 2.2). Relationships use
`lazy="raise"`; sessions use `expire_on_commit=False` (code standard 6.4).

### 5.1 Provided tables

`Schools`, `Users`, `Products`, `Purchase_History`.
**DATA-1** `Products.image_url` (nullable text) is added (D-071). The
supplied and seeded catalog **is** the participating catalog; there is no
participation field (D-090). The supplied legacy chat table,
`Conversation_History`, is dropped by the migration: Capper's own
`messages` and `model_messages` replace it, and nothing reads it (Sam,
D-092).

### 5.2 New tables

- **DATA-2 `turns`**: `id`, `user_id`, `status` (`in_progress`,
  `complete`, `stopped`, `error`), `idempotency_key`, `request_text_hash`
  (to detect a reused key with different text) **(TDD default)**, `model`,
  `content_version`, `app_version` (the package version, plus the git SHA when
  available) **(TDD default)**, `started_at`, `ended_at`. Unique (`user_id`,
  `idempotency_key`). Partial unique index on `user_id` where
  `status = 'in_progress'` (D-046, D-063, D-090).
- **DATA-3 `messages`** (the user-facing transcript, append-only):
  `id`, `user_id`, `turn_id`, `role` (`user`, `assistant`), `parts` (JSON:
  ordered text and card parts exactly as sent), `created_at` (D-056, D-063,
  code standard 5.1). The user message is written at turn start (API-3). The
  assistant message is written once, at turn end, only if the turn produced
  at least one part (API-12).
- **DATA-4 `messages_fts`**: an FTS5 virtual table (`text`, `user_id`
  UNINDEXED, `message_id` UNINDEXED), tokenizer `porter unicode61`, written in
  the same transaction as each message; only text parts are indexed (D-074).
- **DATA-5 `model_messages`** (the model's history, append-only): `id`,
  `user_id`, `turn_id`, `seq`, `payload` (Pydantic AI's serialized message),
  `created_at` (D-071, D-046). The turn's user prompt (a `ModelRequest`
  holding only the user's text) is written at turn start; the run's other
  new messages at turn end.
- **DATA-6 `summaries`**: `id`, `user_id`,
  `covers_through_model_message_id` (the watermark), `text` (the summary,
  heading-checked), `payload` (the serialized summary message),
  `model`, `content_version`, `created_at`. The latest row per user is in use
  (D-043, D-090, D-091).
- **DATA-7 `guidance_notes`**: `id`, `user_id`, `text` (≤ 300 chars),
  `expires_at` (nullable), `created_at`, `updated_at`. Removal deletes the row
  (D-051, D-068).
- **DATA-8 `avoided_products`**: `user_id`, `product_id`, `created_at`;
  primary key (`user_id`, `product_id`) (D-051, D-068).
- **DATA-9 `content_documents`**: `id`, `name`, `content_class`
  (`operator_policy`, `user_knowledge`), `load` (`always`, `on_demand`,
  `app`), `body`, `content_hash`, `active`, `ingested_at`. Partial unique
  index on `name` where `active`. `load = app` means read by the app and
  never sent to the chat model as instructions (the greeting, the summary
  template, the safety-check prompt) **(TDD default: the `app` value)**
  (D-050, D-071, D-090).
- **DATA-10 `promotions`**: `id`, `product_id`, `title`, `description`,
  `starts_at`, `ends_at` (D-071, D-057).
- **DATA-11 `referral_codes`**: `user_id` (unique), `code` (unique),
  `created_at` (D-071).
- **DATA-12 `tool_calls`** (audit log): `id`, `user_id`, `turn_id`,
  `tool_name`, `arguments` (JSON, personal data redacted), `status` (`ok`,
  `error`), `latency_ms`, `created_at` (code standard 3.5).
- **DATA-13 `message_feedback`**: `id`, `user_id`, `message_id`, `rating`
  (`up`, `down`), `comment` (≤ 500 chars, nullable) **(TDD default length)**,
  `created_at`, `updated_at`; unique (`user_id`, `message_id`); a new rating
  replaces the old (D-076).

### 5.3 Rules

- **DATA-14** Transactions are short and never held across a model call or a
  stream; writes happen at defined points: turn start, each tool call's audit
  row, turn end (code standard 6.3).
- **DATA-15** The content version is a SHA-256 over the active rows' (`name`,
  `content_class`, `load`, `content_hash`) tuples, sorted by name, so a change
  to how a document is loaded is a new version too **(TDD default for the
  exact formula)** (D-050).
- **DATA-16** Publishing content inserts new rows and clears the previous
  rows' `active` flag in the same transaction; published `body` text is never
  updated (D-090).

### 5.4 Migrations

**DATA-17** One Alembic migration creates DATA-1 to DATA-13, including the
FTS5 table and partial indexes (raw SQL where SQLAlchemy has no construct),
and drops `Conversation_History` (DATA-1). *Check:* `alembic upgrade head` on
the provided database succeeds, and `alembic downgrade base` removes the new
tables and column and recreates `Conversation_History` with its original
schema (empty; the legacy rows aren't restored).

### 5.5 Seeds (mvp-plan #5; D-008, D-027, D-070, D-071)

**DATA-18** The bootstrap's seed step (`scripts/seed.py`) loads, idempotently:
1. Extra products, including those shown in the mockups (D-008), with
   `image_url` values for all products: the path of the product's SVG image,
   shipped in the package and served by the app (API-6, D-094)
   **(TDD default: illustrative SVGs, since the supplied catalog has no
   images)**. Products get only the generic fields
   the tools need; no domain-specific or category fields (D-057, D-058).
2. A few active promotions on seeded products.
3. Referral codes for every seed user except one (the "no code" case).
4. Purchases across several users at the same schools, so popular products
   has something to rank (D-070).
5. Seed users (D-027): an established user (school, purchases, referral
   code); a new user with nothing (no purchases, no school, no guidance, no
   code); a user with guidance notes and avoided products, one note an
   allergy (D-027; the fixture for "health guidance never becomes a safety
   guarantee", D-057); two users with parallel data for cross-account specs.

## 6. Content and ingestion (mvp-plan #3, #4)

### 6.1 Documents to author (mvp-plan #3)

**CNT-1** Source files under `content/source/` **(TDD default path)**,
listed in `content/manifest.toml` (the allowlist, D-049). Authored by us,
flagged as such; assumptions and boilerplate are fine (D-049):

| Name | Class | Load | Contents (decisions) |
|---|---|---|---|
| `scope_charter` | operator_policy | always | What Capper is for and isn't; questions the content can't answer are handed off to support, never guessed (D-049, D-054) |
| `persona_voice` | operator_policy | always | Capper's voice (D-034); English only (D-069); when data is thin, a short acknowledgement that Capper learns the user's habits as they use the app, or an invitation to say what they're interested in (D-070); products are referred to only through cards, never named from memory (D-056); guidance personalizes within scope and safety rules; newer notes supersede older (D-051, D-067); save clear requests and say what was saved (D-051); on removal, the exact wording D-051 fixes: "I removed that from your saved guidance"; a sensitive detail in a note (such as a health condition) is remembered and never turned into a safety guarantee (D-051, D-057); when a list result is partial, state how many are shown out of the total (D-080, D-092) |
| `do_no_harm_core` | operator_policy | always | The always-on core (no specialized medical, legal or financial advice; no guessing on health or safety facts; crisis → resources and hand-off), the trigger line to call `read_document` for a policy, and the list of on-demand policy names it can read (D-049) |
| `policy_*` (one per area) | operator_policy | on_demand | One detailed policy per topic D-049 lists: allergens and food safety, dietary and medical claims, child safety, product misuse, crisis. The topics are content only; nothing in code knows them (D-049, D-057) |
| `referral_faq`, `program_rules` | user_knowledge | always | Hand-curated from the PDFs: where they conflict the Rules win, as a flagged demo assumption; example values ("e.g. $5", "e.g. 48 hours") marked as examples (D-053, D-055) |
| `product_knowledge` | user_knowledge | always | The app behaviors the demo flows need (the referral page, Bonus Caps, scanning receipts, linking a school) and support contact details for hand-off; authored by us and flagged (D-035, D-054, D-058) |
| `greeting` | operator_policy | app | The greeting bubbles shown when the chat opens (D-060) |
| `compaction_summary_template` | operator_policy | app | The summary prompt with required headings: goals and constraints the user stated, IDs mentioned, open questions; requests recorded as reported speech (D-077, D-091) |
| `safety_check_instructions` | operator_policy | app | The prompt for the safety-net check (§11) **(TDD default: as content)** |

*Check:* every name above exists, active, after ingestion; no internal-only
content is listed in the manifest; the policy names listed in
`do_no_harm_core` match the on-demand documents.

### 6.2 Ingestion (mvp-plan #4)

- **ING-1** The `ingestion` package reads `content/manifest.toml` (each
  entry: `name`, `class`, `load`, source file), loads each listed Markdown
  file, normalizes whitespace, computes `content_hash` (SHA-256 of the body),
  and publishes through `content_bundle` (DATA-16). Files not in the manifest
  are ignored (D-049). MVP sources are Markdown (the PDFs are curated into
  Markdown by hand, D-053), so no PDF parser is used **(TDD default)**.
- **ING-2** A document whose `name`, `class`, `load` and `content_hash` are
  all unchanged is not republished; a change to any of them publishes a new
  row. A document removed from the manifest (the allowlist) is deactivated
  (D-049, D-092).
- **ING-3** The bootstrap runs it (ENV-9); a content change takes effect on the
  next turn with no deploy or restart (D-050).

### 6.3 Reading content

- **ING-4** `content_bundle` exposes: read the active set (name, class, load,
  body) and its content version; publish a set. Nothing else (D-032,
  D-050).

### 6.4 The content snapshot

- **ING-5** At the start of each turn the service reads the active set once
  into `CapperDeps`. Instructions, `read_document` and the safety check all
  use that snapshot, even if ingestion publishes mid-turn (D-050, D-090).
  The turn records the snapshot's content version, the model and the
  `app_version` (DATA-2), and its messages link to the turn (code standard
  4.4). Prompts that live in content are versioned by the content version;
  prompt text that lives in code (tool descriptions, the turn-context block's
  wording) is versioned by `app_version`.

## 7. Authentication (mvp-plan #6; D-020)

- **AUTH-1** Every endpoint except the demo page's static files and the two
  demo sign-in routes (AUTH-5) requires `Authorization: Bearer <JWT>`. The service is a stateless resource server:
  it verifies signature (algorithm pinned to RS256 **(TDD default)**), `exp`,
  `iss` and `aud` locally against a configured public key, and takes `sub` as
  the user ID. No session state, no call to the auth API per request (D-020,
  D-084).
- **AUTH-2** A valid token for a user not in `Users` is rejected (401)
  (D-020).
- **AUTH-3** `user_id` comes only from the verified token; never from a body,
  URL or tool argument (code standard 2.1).
- **AUTH-4** Login is not Capper's job. In production the app's existing
  auth API and login portal sign the user in, and the app sends Capper the
  resulting access token; Capper only verifies it (D-020). The auth API in
  the brief is hypothetical, so the MVP has no login, no simulated login, no
  stubbed auth API and no separate service (Sam, D-092).
- **AUTH-5 Demo sign-in, the one exception to code standard 1.1** (Sam,
  D-092). Capper stands in for the *result* of login:
  1. `GET /demo/users` → the users in `Users` (`id`, `name`, school name),
     sorted by name.
  2. `POST /demo/sessions`, body `{user_id}` → `{access_token, expires_at}`:
     a token for that user, signed with the dev private key, with exactly
     the claims the real auth API's token would carry (`sub`, `iss`, `aud`,
     `exp`; lifetime `demo_session_minutes`, 60 **(TDD default)**). Unknown
     user → 404.
  3. Nothing else is different. Every other request verifies that token
     through AUTH-1 to AUTH-3, and the account, records and tools load from
     the verified user exactly as they would in production.
  4. Both routes need no token; they are flagged in the README and in
     `future-considerations.md` as the demo stand-in for the auth API, to be
     removed when Capper meets a real one.
- *Checks (D-020 edge cases):* missing, malformed, bad signature, `alg`
  confusion and `none`, expired, wrong `iss`, wrong `aud`, unknown user → 401.

## 8. Tools (mvp-plan #7–15, #34; D-058, D-059, D-070, D-074, D-080, D-088, D-090)

### 8.1 Rules for every tool

- **TOOL-1** Strict schemas (required fields, no extra properties); inputs
  validated before execution (code standard 3.1).
- **TOOL-2** `user_id` from `CapperDeps` only; no tool has a `user_id`
  parameter (code standard 2.1).
- **TOOL-3** A shared adapter wraps every tool call: it writes the
  `tool_calls` audit row (redacted arguments, status, latency) in its own
  short transaction, enforces the per-turn tool-call limit, and enforces the
  result size cap (code standards 3.5, 6.3).
- **TOOL-4 Per-turn tool-call limit** `max_tool_calls_per_turn` (10) (D-043,
  D-064):
  1. The adapter counts calls in `CapperDeps`. Calls beyond the limit, even
     within one parallel batch, are not executed; each returns the explicit
     result "tool-call limit reached; answer with what you have".
  2. Once the limit is reached, the next model request is made with tool use
     disabled (tool choice `none`; the definitions stay the same, TOOL-8), so
     the model must answer in text **(TDD default; mechanism in Appendix B)**.
  3. Backstop: the run's Pydantic AI `UsageLimits` caps model requests at the
     limit + 2 **(TDD default)**; exceeding it ends the turn with the generic
     error (API-9).
- **TOOL-5** Result size cap `tool_result_max_chars` (8,000) **(TDD
  default)**: a result over it returns an explicit "result too large, narrow
  the request" error result, never a silent cut (D-088).
- **TOOL-6** Errors are returned to the model as error results, never raised
  through the conversation (code standard 3.6).
- **TOOL-7 Cursor contract** for tools that enumerate records (D-080):
  1. `limit` (default 10, max 50 **(TDD default)**), opaque keyset `cursor`;
     results `{items, total_count, next_cursor}`; no `next_cursor` means the
     end.
  2. Every list has a deterministic order ending in a unique key, so keyset
     paging is stable **(TDD default orders)**: products by name, then ID;
     promotions by `ends_at`, then ID; purchases by `purchased_at`
     descending, then ID descending; popular products by purchase count
     descending, then product ID.
  3. `total_count` answers "how many" questions without paging (D-043); the
     tool description says so, and tells the model to state how many are
     shown out of the total when a list is partial.
  4. History search is exempt (D-090).
- **TOOL-8** Tool definitions never change per request (code standard 4.2).
  `read_document`'s `name` is a string, not a per-snapshot enum; it is
  validated against the turn's snapshot when the tool runs (D-090).

### 8.2 The tools

| Tool | Inputs | Returns | Rules |
|---|---|---|---|
| `search_products` (#7) | `query` (optional text), `limit`, `cursor` | Products: `id`, `name`, short description (≤ 200 chars **(TDD default)**), `price`; cursor fields | Case-insensitive match on name and description **(TDD default)**; avoided products always excluded in the query (D-051); cursor contract |
| `get_promotions` (#8) | `limit`, `cursor` | Active promotions (`starts_at ≤ now < ends_at`): `id`, `product_id`, `title`, `description`, `ends_at`; cursor fields | Excludes promotions on avoided products; cursor contract |
| `get_my_referral_code` (#9) | none | `{code}` or `{code: null, reason: "no_code"}` | Never invents a code |
| `get_my_purchases` (#10) | `limit`, `cursor` | Purchases newest first: `product_id`, `product_name`, `quantity`, `purchased_at`; cursor fields | Cursor contract (D-059) |
| `get_popular_products` (#11) | `limit`, `cursor` | `{basis: "school" or "overall", items: [{product_id, name, purchase_count}], total_count, next_cursor}` | Aggregate counts only, no other users' identities or purchases; ranked among users at the user's school, or all users if no school; avoided products excluded; an empty list is acceptable; cursor contract (D-070, D-090) |
| `search_my_history` (#12) | `query` | Up to 5 matches: `message_id`, `created_at`, `role`, `snippet` | FTS5 `MATCH` plus `user_id` filter in the same query; ranked by `bm25`; query quoted term by term; results marked as user data; no cursor; cards not searchable (D-074, D-090) |
| `read_document` (#13) | `name` (string) | The document body | Must name an `on_demand` document in the turn's snapshot, else an error result listing the valid names; reads the snapshot only (D-058, D-090) |
| `show_products` (#7) | `product_ids` (1–10 **(TDD default)**), `heading` | `{shown: n}` to the model; a `card` event to the app | Validates every ID exists and isn't avoided; builds the card from database records (`id`, `name`, `price`, `image_url`); unknown or avoided IDs → error result naming them, no card (D-056) |
| `show_promotions` (#8) | `promotion_ids` (1–10), `heading` | As above | Validates each promotion is active and its product isn't avoided; card shows title, description and the product's image (D-056) |
| `avoid_product` / `unavoid_product` (#14) | `product_id` | The saved change | Product must exist; cap `avoid_list_max` (100) → explicit "list full" result (D-051, D-068) |
| `add_guidance` (#15) | `text` (≤ 300), `expires_at` (optional date) | The saved note with its ID | Cap `guidance_max_notes` (30) → explicit "guidance full" result; the description asks for a short, consistent statement (D-068) |
| `update_guidance` (#15) | `note_id`, `text`, `expires_at` (optional) | The updated note | Note must belong to the user (else "not found") |
| `remove_guidance` (#15) | `note_id` | Confirmation | Same scoping |

*Not tools* (D-058): hand-off (content); lists or plans the user asks for
(composed replies, D-054, D-057); the user's name and school, guidance and
the avoid list (all in context).

*Check:* the registered tool set is exactly these 14: `search_products`,
`get_promotions`, `get_my_referral_code`, `get_my_purchases`,
`get_popular_products`, `search_my_history`, `read_document`,
`show_products`, `show_promotions`, `avoid_product`, `unavoid_product`,
`add_guidance`, `update_guidance`, `remove_guidance`.

## 9. Context assembly (mvp-plan #17; D-072, D-090, code standards 4.2, 4.6)

**CTX-1** Each model request is assembled from loaded data by pure functions,
in this order:

1. **Instructions:** the active `always` operator-policy documents, then the
   `always` user-knowledge documents, from the snapshot. Byte-identical for a
   given content version (code standard 4.2).
2. **Tool definitions:** the fixed set (§8).
3. **Account context** *(request-only, CTX-2)*: a user-role data block
   clearly marked as user-supplied data: the user's name and linked school;
   guidance notes in order with their dates (expired notes omitted); the
   avoid list. Never interpolated into instructions (code standard 4.6)
   **(TDD default: placed before the history)**.
4. **History:** the latest summary message, if any, then every
   `model_messages` row after its watermark, in order (D-090). It ends with
   this turn's user prompt, stored at turn start (API-3), and grows with the
   run's own messages.
5. **Turn context** *(request-only, CTX-2)*, placed immediately before this
   turn's user prompt: a user-role data block with the current local time
   (the default time zone, D-060); and, if the safety net flagged a policy
   (§11), that policy's text from the snapshot as a separate, clearly
   labeled operator part (a system-role part) **(TDD default)** (D-090).

**CTX-2 Request-only injection.** Account context and turn context are added
by the last capability in the chain (AGT-7), after clearing and compaction,
to the outgoing request only. They are never in the run's message history, so
they are never persisted to `model_messages`, never summarized, and never
counted toward the history budget. Everything before the history stays a
stable prefix across turns; the turn context sits after it.

**CTX-3** The greeting is never in the history (D-060).

**CTX-4** Summaries and history-search results are user-derived text and are
always treated as data (code standard 4.6).

**CTX-5** No app-side caches of documents, live data or model answers: content
is read once per turn (ING-5), live data comes from tools, and answers are
never reused across requests or users. The only cache is the provider's prompt
cache with the per-user opaque key (AGT-5) (code standard 4.8, D-050).

## 10. Context budget, clearing and compaction (mvp-plan #21–23; D-043, D-064, D-065, D-087, D-089, D-090, D-091)

- **CMP-1 Budget.** `history_budget_tokens` (20,000). The compaction trigger
  is 75% of it, enforced through the Harness token trigger. `keep_tokens` is
  a floor on what compaction keeps verbatim, set from the ~40% target; the
  target is a tuning value, not a guarantee (D-090). Counts anchor on the
  provider's reported usage, with the Harness estimate for messages since.
  Request-only blocks (CTX-2) are outside the budget.
- **CMP-2 Size check before every model call** is the Harness trigger
  evaluation; `ReportContextUsage` records usage on the turn's trace (D-089,
  D-079).
- **CMP-3 Clearing.** `ClearToolResults` with `keep_pairs` =
  `max_tool_calls_per_turn` + `tool_results_kept` (10 + 5), tool calls left
  visible (`clear_tool_inputs=False`), `min_clear_tokens` set (2,000 **(TDD
  default)**) so clearing isn't triggered for a trivial gain. It protects the
  whole active turn and at least the five most recent past-turn results;
  re-running a cleared tool is a fresh read (D-065, D-087, D-090).
- **CMP-4 Compaction.** The Harness `SummarizingCompaction` on the compaction
  model (`openai:gpt-6-luna`, D-047), configured with:
  1. `summary_prompt` from the `compaction_summary_template` document;
  2. `keep_tokens` (CMP-1);
  3. `preserve_first_user_message=False` and `keep_user_messages=False`: the
     first message is just an old prompt (account context is request-only,
     CTX-2), and every older message, user or not, is summarized;
  4. `retries=1`, each attempt recorded on the trace (code standard 8.5);
  5. its own token trigger, the compaction trigger (CMP-1). It summarizes
     before the request that crosses the trigger; nothing is prepared in the
     background (D-096).
  No sliding-window or other lossy fallback, and no strategy wrapper that
  swallows a failure (for example a tiered `skip_on`): if summarizing fails,
  the turn fails with the generic error (D-043, D-061).
- **CMP-5 Heading check.** An output validator on the summarizer checks that
  every required heading from the template is present (a pure function). A
  missing heading is a retry (within CMP-4's one retry); if it still fails,
  compaction raises, no summary is applied or saved, and the turn fails
  visibly with the generic error (D-091) **(TDD default: validator on the
  summarizer, Appendix B)**.
- **CMP-6 Over the model's limit.** Clearing and compaction keep history near
  the budget, but the active turn is protected and can grow past it. No
  app-side pre-send estimator is built: OpenAI's truncation stays disabled
  (the default), so a request over the model's input limit is rejected by the
  provider and the turn ends with the generic error (API-9). Nothing is ever
  silently truncated. The trace shows the usage (CMP-2).
- **CMP-7 Persistence, by position.** At turn end, after the run's new
  messages have rows: if the run compacted, its history is
  `[summary] + suffix`, where `suffix` is the last `len(history) − 1`
  messages of the full list the run worked on (the loaded history plus the
  run's new messages). The watermark is the row of the last message **not**
  in the suffix. Messages are matched by position, never by comparing
  payloads. If that message is the previous summary itself, the new summary
  keeps the previous watermark. The service saves a `summaries` row with the
  watermark, the summary text, its serialized message, the compaction model
  and the content version (D-090). The transcript (`messages`) is never
  touched.
- **CMP-8 Reload** is CTX-1 step 4; the loaded list may start with the
  previous summary, which a later compaction folds into the new one.
- **CMP-9 Lifecycle.** Removed with the background start (D-096): compaction
  runs inside the request that needs it, so nothing outlives a run.
- *Check:* the deterministic compaction specs (TEST-9).

### 10.1 Worked sequence: compaction to persisted reload

1. Turn *n* loads `[S1, m41 … m60]` (S1 = the latest summary, watermark
   m40) and adds the turn's prompt m61 (stored at turn start).
2. Before a model request, the Harness trigger fires (≥ 75% of the budget).
   Clearing runs first; it isn't enough.
3. The summarizer receives `[S1, m41 … m52]`, keeps `[m53 … m61, new]`
   verbatim (at least `keep_tokens`), and returns S2. Its headings are
   checked (CMP-5).
4. The model request goes out as `[S2, m53 … m61, new]` plus the request-only
   blocks (CTX-2).
5. Turn end, one transaction: the run's new messages become m62 … m65; the
   suffix is `[m53 … m65]`, so the watermark is m52; S2 is saved with it.
6. Turn *n + 1* loads `[S2, m53 … m65]`. Compacting again repeats the
   sequence with S2 as the first message.

## 11. Do-no-harm safety net (mvp-plan #40; D-049, D-090)

- **SAFE-1** A check agent on the compaction model runs concurrently with
  context building and is awaited before the turn's first model request.
  Input: the user's message and the list of on-demand policy names from the
  snapshot. Output: a structured list of policy names that should be loaded
  (validated against that list) **(TDD default: native structured output,
  reasoning off, a 200-token output cap)**. Every turn waits for it, so its
  speed is part of every reply's latency.
- **SAFE-2** Timeout `safety_check_timeout_seconds` (2 s). A flagged policy
  goes into that turn's turn-context block (CTX-1 step 5), never into the
  instructions. On failure or timeout the turn proceeds without it (fail
  open) and the trace records it (D-090).
- **SAFE-3** A simple proof of concept, not a robust, graded system
  (mvp-plan #40). The always-on core and trigger line still apply.

## 12. API (mvp-plan #16, #18–20, #27; D-063, D-076, D-090)

All JSON uses snake_case; times are ISO 8601 UTC. FastAPI generates the
OpenAPI document.

### 12.1 Endpoints

- **API-1 `GET /v1/conversation`** → `{greeting: [string], turn_in_progress:
  bool, active_turn_id: string | null}` (D-060, D-063).
- **API-2 `GET /v1/conversation/messages?before=&limit=`** → `{messages,
  next_cursor}`, newest first; `limit` default 20, max 100 **(TDD
  default)**. A message: `id`, `role`, `created_at`, `status` (the turn's
  status, for both roles), `parts` (D-063).
- **API-3 `POST /v1/conversation/messages`**, body `{text}`, header
  `Idempotency-Key` (required **(TDD default)**) → `200
  application/x-ndjson`. In order:
  1. Validate: empty text or more than `max_message_chars` (8,000) → 422
     (D-043, D-064).
  2. Same key and text: running → 409 `turn_in_progress`; ended → 200
     replaying the stored turn (API-14), no model call. Same key, different
     text → 422 `idempotency_key_reused` (D-090).
  3. Another turn running → 409 `turn_in_progress` with its turn ID (the
     partial unique index makes this race-safe).
  4. Start the turn in one transaction: the turn row (`in_progress`, with
     content version, model and `app_version`), the user's message with its
     FTS row, and the user prompt as a `model_messages` row; commit before
     generation (D-090). A crash after this point still leaves the prompt in
     both the transcript and the model history.
- **API-4 `POST /v1/conversation/turns/{turn_id}/stop`** → 202
  `{stopped: bool}`; another user's turn → 404; an ended turn →
  `{stopped: false}` (D-090).
- **API-5 `POST /v1/conversation/messages/{message_id}/feedback`**, body
  `{rating: "up" | "down", comment?}` → 200 with the saved feedback; only
  assistant messages, only the user's own (else 404); replaces an earlier
  rating (D-076).
- **API-6 `GET /`** serves the demo page (same origin, no CORS) (D-077);
  the demo sign-in routes are AUTH-5. `GET /images/products/{file}` serves
  the product images that cards reference (D-094).
- **API-15 `GET /healthz`** → `200 {"status": "ok"}` when the database
  answers, else `503`; no token needed (D-094) **(TDD default path)**.

### 12.2 The stream (D-056, D-063, D-090)

- **API-7 Events**, one JSON object per line with a `type`:
  `turn.start {turn_id, user_message_id}`, `text.delta {text}` (Markdown),
  `card {card_type: "product" | "promotion", heading, items}`,
  `turn.end {status: "complete" | "stopped", assistant_message_id: string |
  null}`, `error {code: "generic", message}` (terminal) **(TDD default: where
  the message IDs appear)**. `assistant_message_id` is null when the turn
  produced no parts (DATA-3).
- **API-8 Bubbles** are the app's job: it splits text at paragraph breaks and
  around cards (D-063).
- **API-9 Error channels.** Before streaming: HTTP status with
  `{"error": {"code", "message"}}`. After streaming begins: one `error`
  event, the stream ends, the turn is `error`, and what happened is saved
  (API-14) (D-061, D-090). The message is generic and never names the
  provider (D-033).

### 12.3 Turn lifecycle (D-046, D-072, D-090)

- **API-10** Generation runs in a background task owned by the app's
  lifespan; the response streams from a queue the task fills. A client
  disconnect doesn't cancel the task; the turn finishes and is saved
  (D-046). On shutdown the app waits for running turns up to the turn
  timeout, then cancels any still running and marks them `error` (code
  standard 6.6) **(TDD default for the cancel-after-timeout step)**.
- **API-11 Stop** looks up the turn's cancellation token (held in an
  in-process map keyed by turn ID) and cancels the run; Pydantic AI's
  interrupted state is kept (D-046). The turn then ends as `stopped`
  (API-14).
- **API-12 Turn end** writes, in one transaction: the assistant message if
  any parts were produced (parts as sent) with its FTS row, the run's new
  `model_messages` (API-14), a summary if the run compacted (CMP-7), and the
  turn's status and `ended_at`. The transaction **commits before** the
  terminal event (`turn.end` or `error`) is emitted, so a client that
  reloads on the terminal event always sees the saved turn.
- **API-13** Domain exceptions are mapped to HTTP responses in one place
  (code standard 6.5).
- **API-14 Outcomes.** One table governs the live stream, what is saved, and
  the replay of a duplicate send:

| Status | Live stream ends with | Transcript saved | Model history saved | Replay (API-3 step 2) |
|---|---|---|---|---|
| `complete` | `turn.end {complete, id}` | the assistant message | the run's new messages | `turn.start`, stored parts, `turn.end {complete, id}` |
| `stopped` | `turn.end {stopped, id or null}` | parts sent before the stop, if any | the run's new messages up to the stop | `turn.start`, stored parts, `turn.end {stopped, id or null}` |
| `error` | `error {generic}` | parts sent before the failure, if any | the run's new messages up to the failure | `turn.start`, stored parts, `error {generic}` |
| `error` (startup recovery, ENV-8) | (no live stream) | nothing beyond the user message | nothing beyond the user prompt | `turn.start`, `error {generic}` |

  In the stopped and error rows, a tool call left without a result is stored
  as it happened, with Pydantic AI's interrupted state. The framework closes
  it with an interrupted result when the history is next sent, so the next
  request is valid and the model can see what was interrupted (code standard
  6.2). Nothing the model produced is dropped (D-095).

### 12.4 Demo page (mvp-plan #27; D-019, D-077)

- **DEMO-1** A static page (vanilla JS, no build step, styled after the
  mockups) served at `/`: a sign-in screen listing the users (AUTH-5), where
  clicking one creates the session and the page keeps the token in memory
  and sends it as the bearer token; sign out returns to the list. Then the
  greeting, history loading, a
  message box whose send button becomes a stop button while a turn runs,
  streamed text, product and promotion cards, and thumbs up/down per
  assistant message.
- **DEMO-2** Markdown is rendered with HTML escaped first; no raw HTML from
  model output ever reaches the DOM (code standard 6.7). Supported subset
  **(TDD default)**: paragraphs, bold, italic, bulleted and numbered lists,
  headings. Links are shown as plain text with their URL; images are not
  rendered.

## 13. Configuration (ENV-5)

| Setting | Default | Source |
|---|---|---|
| `database_url` | `sqlite+aiosqlite:////app/data/capper.db` | D-045, D-094 |
| `chat_model` | `openai:gpt-6.1-terra` | D-047 |
| `compaction_model` | `openai:gpt-6-luna` | D-047 |
| `OPENAI_API_KEY` | none | interviewer answer 1 |
| `model_connect_timeout_seconds` | 5 | D-061 (TDD default value) |
| `turn_timeout_seconds` | 60 | D-061 (TDD default value) |
| `history_budget_tokens` | 20,000 | D-064 (TDD default value) |
| `compaction_trigger_ratio` | 0.75 | D-043 |
| `compaction_target_ratio` | 0.40 | D-043, D-090 |
| `tool_results_kept` | 5 | D-065 |
| `max_tool_calls_per_turn` | 10 | D-064 (TDD default value) |
| `min_clear_tokens` | 2,000 | (TDD default) |
| `tool_result_max_chars` | 8,000 | D-088 (TDD default value) |
| `max_message_chars` | 8,000 | D-064 (TDD default value) |
| `max_output_tokens` | 4,096 | D-064 (TDD default value) |
| `output_retries` | 1 | D-064 |
| `guidance_max_notes` | 30 | D-068 |
| `guidance_max_chars` | 300 | D-068 |
| `avoid_list_max` | 100 | D-068 |
| `safety_check_timeout_seconds` | 2 | D-090 |
| `default_timezone` | `UTC` | D-060 |
| `cache_key_secret` | none (required) | (TDD default) |
| `jwt_public_key_path`, `jwt_private_key_path` (the latter for demo sessions only, AUTH-5) | `/app/data/keys/dev_public.pem`, `/app/data/keys/dev_private.pem` (created by the bootstrap) | D-020, D-092, D-094 |
| `jwt_issuer`, `jwt_audience` | `carton-caps-auth`, `capper` | D-020 (TDD default values) |
| `demo_session_minutes` | 60 | D-092 (TDD default value) |
| `otlp_endpoint` | `http://traces:4318` | D-079 (TDD default value) |
| `model_prices` (per million tokens: input, cached input, output) | Terra $1 / $0.05 / $5; Luna $0.10 / $0.01 / $0.50 | D-047 research (TDD default values; configurable estimates for the trace's cost attribute, not billing) |

A validator keeps `0 < target < trigger ≤ 1`.

## 14. Observability (mvp-plan #32; D-064, D-075, D-079)

- **OBS-1** OpenTelemetry tracing via Pydantic AI's `Instrumentation`
  capability with `include_content=False`, exported over OTLP HTTP to the
  `traces` container (D-079, code standard 5.2).
- **OBS-2** One root span per turn (`capper.turn`) with attributes: opaque
  user key, turn ID, model, content version, app version, input / output /
  cached tokens, estimated cost (tokens × `model_prices`), time to first
  token (counted from the turn's start, so it includes the safety check's
  wait), the safety check's outcome and wait (`capper.safety_outcome`,
  `capper.safety_wait_ms`), tool-call count, whether clearing or compaction
  ran, final status (D-075).
- **OBS-3** Span events for each budget check, clearing, compaction, retry,
  error and safety-check outcome (D-064, D-090).
- **OBS-4** No message content in spans or logs. Plain stdout logging only
  for startup and unexpected errors, through module-level loggers (code
  standard 8.6).
- *Check:* a turn's trace shows the root span, model and tool spans, and the
  attributes above; no prompt or reply text appears anywhere in it.

## 15. Security (D-077, code standards §2–§3)

- **SEC-1** Cross-account access is impossible through every endpoint and
  tool (code standards 2.1, 2.2, 2.4); IDs in URLs return 404 for other users.
- **SEC-2** User text is data, never instructions, including stored text
  that comes back (code standard 4.6, CTX-1, CTX-4).
- **SEC-3** Summaries record user requests as reported speech (D-077, CNT-1).
- **SEC-4** `pip-audit` runs clean (D-077).
- **SEC-5** Markdown is rendered without raw HTML (code standard 6.7).
- **SEC-6** No secrets in the repository; `.env` ignored (ENV-5).

## 16. Specs and evals (mvp-plan #28–30; D-062, D-090)

Specs use Pydantic AI's `TestModel` / `FunctionModel` injected from the test
suite, `ALLOW_MODEL_REQUESTS = False`, and a temporary database per test; no
spec touches the network (code standards 1.1, 8.8).

- **TEST-1 Auth:** every D-020 edge case (§7); a demo session token passes
  the same verification as any other; the AUTH-5 routes are the only API
  routes that accept no token.
- **TEST-2 Cross-account:** for every endpoint and every tool touching user
  data, user A can't read or change user B's data (SEC-1).
- **TEST-3 Tools:** schema validation; the avoid-list filter in search,
  promotions, popular products and cards; card building from records;
  unknown and avoided IDs rejected; `read_document` rejects a name not in the
  snapshot; caps (guidance, avoid list, result size) return explicit results;
  the tool-call limit (calls past it in one batch get the limit result, the
  next request has tool use disabled, the backstop ends the turn); the cursor
  contract (totals, `next_cursor`, end of results, stable order across pages)
  and the tool descriptions mention totals and cursors; history search
  scoping and query quoting (§8).
- **TEST-4 Content:** ingestion publishes only manifest documents;
  republishing flips `active` atomically; a change to `class` or `load` alone
  republishes and changes the content version; the content version doesn't
  change when nothing changed; a turn uses one snapshot even if content is
  published mid-turn (§5.3, §6).
- **TEST-5 Context assembly:** order and contents (CTX-1); guidance in a data
  block, never in instructions; expired notes omitted; a flagged policy in
  the turn-context block, not the instructions; account and turn context are
  absent from `model_messages` and from the summarizer's input (CTX-2).
- **TEST-6 Turn lifecycle:** one active turn (409); duplicate sends (409,
  replay, 422); replay matches API-14 for each status; the user message and
  user prompt are committed before generation; startup marks stale turns
  `error`; the terminal event is emitted only after the turn is committed.
- **TEST-7 Stop/continue regression:** stop a reply, send a follow-up that
  narrows the stopped request, and verify the new run still has the original
  request in context (D-046; D-046's fixture text is "Actually, just
  snacks").
- **TEST-8 Errors:** a pre-stream failure is an HTTP error; an in-stream
  failure is one terminal `error` event, the turn is `error`, and what is
  saved matches API-14 (every tool call in the stored history has a result,
  synthetic if interrupted).
- **TEST-9 Compaction** (deterministic, a `FunctionModel` summarizer):
  1. *Persistence:* after a compacting run the transcript is unchanged;
     reload yields the summary plus exactly the messages after the
     watermark; tool calls and results stay paired.
  2. *Cycle:* compact → persist → reload → compact again (§10.1), checking
     the watermark each time and that the previous summary is folded in.
  3. *Headings:* a summary missing a required heading is retried, then
     fails the turn with nothing saved (D-090, D-091).
  4. *Isolation:* runs carry the user's opaque key as `conversation_id`.
- **TEST-10 Clearing configuration:** the active turn's results are never
  cleared, and at least five past-turn results remain (CMP-3).
- **TEST-11 Safety net:** a flag adds the policy to the turn context; a
  timeout or failure proceeds without it and is recorded (§11).
- **TEST-12 Feedback:** create, replace, scoping, only assistant messages
  (API-5).
- **TEST-13 Agent settings:** AGT-3 values on the built request; the prompt
  cache key is the opaque key, never the internal user ID; no context block
  the app builds contains the internal user ID.
- **EVAL-1 Tool-call eval** (`evals/`, Pydantic Evals, real model, explicit
  command only, seeded database copy): messages touching health or safety
  call `read_document` with a fitting policy; an unrelated message doesn't
  (D-062). It measures the agent's own on-demand choice, so the eval composes
  the agent without the safety-net check (the composition is chosen in the
  eval, by dependency injection; production code has no switch for it, D-007).
- **EVAL-2 Answer-quality eval with an LLM judge,** implemented, commented
  out, and labeled as an example rather than an executed check (D-062,
  D-090). An example case: a partial list answer states "showing N of M".

## 17. Design documentation deliverables (mvp-plan #44–47, #49)

Written after the build, describing what was built:

- **DOC-1 API contract spec** (#44): §12 in full, generated OpenAPI plus the
  NDJSON event schema and error codes (D-063, D-076, D-090).
- **DOC-2 Onboarding diagrams** (#45): system context (app, Capper, OpenAI,
  traces, database), the request flow (D-072), the content pipeline (D-050),
  context assembly and compaction (D-043, D-089).
- **DOC-3 Mobile integration notes** (#46): token handling, consuming NDJSON,
  idempotency keys, stop by turn ID, reconnecting by reloading, rendering
  Markdown without raw HTML, bubbles and cards (D-063, D-090).
- **DOC-4 Privacy considerations** (#47): what's stored and where, guidance
  notes and their removal, `store: false` and OpenAI's separate retention
  policy, log and trace redaction (D-051, D-052, D-066, D-079).
- **DOC-5 Final summary** (#49): from `future-considerations.md`.

## 18. Build order

1. Environment and Docker (ENV-1 to ENV-11, §2.1, API-15).
2. Data model, migration and seeds (§5).
3. Content documents and ingestion (§6).
4. Auth (§7).
5. Domain services and repositories (accounts, catalog, memory).
6. Tools (§8), agent and context assembly (§4, §9).
7. Conversation API and turn lifecycle (§12.1–12.3).
8. Budget, clearing and compaction (§10, §10.1).
9. Safety net (§11).
10. Observability (§14).
11. Demo page (§12.4).
12. Specs (TEST-1 to TEST-13) alongside each step; evals last (EVAL-1, EVAL-2).
13. Documentation deliverables (§17).

## 19. Traceability: mvp-plan items to this document

| Plan # | Item | Sections / requirements |
|---|---|---|
| 1 | Dockerize | ENV-6 to ENV-9, ENV-11, §2.1, API-15 |
| 2 | Environment and tooling | ENV-1 to ENV-5, ENV-10, §13 |
| 3 | Content authoring | CNT-1 |
| 4 | Ingestion and content table | ING-1 to ING-5, DATA-9, DATA-15, DATA-16 |
| 5 | Schema and seeds | §5 |
| 6 | Auth | AUTH-1 to AUTH-5 |
| 7 | Product search and cards | §8.2 `search_products`, `show_products` |
| 8 | Promotions and cards | §8.2 `get_promotions`, `show_promotions` |
| 9 | Referral code | §8.2 `get_my_referral_code` |
| 10 | Purchase history | §8.2 `get_my_purchases` |
| 11 | Popular products | §8.2 `get_popular_products` |
| 12 | History search | §8.2 `search_my_history`, DATA-4 |
| 13 | Do-no-harm policies on demand | CNT-1, §8.2 `read_document`, TOOL-8 |
| 14 | Avoid list | §8.2, DATA-8 |
| 15 | Guidance notes | §8.2, DATA-7, CTX-1 |
| 16 | Conversation API | API-1 to API-3, API-7 to API-9, API-12 to API-14 |
| 17 | Agent and context builder | §4, §9 (CTX-1 to CTX-5) |
| 18 | Stop; disconnects don't cancel | API-4, API-10, API-11, API-14 |
| 19 | Provider failures | AGT-8, API-9 |
| 20 | User feedback | API-5, DATA-13 |
| 21 | Context budget | CMP-1, CMP-2, CMP-6 |
| 22 | Tool-result clearing | CMP-3 |
| 23 | Compaction | CMP-4, CMP-5, CMP-7, CMP-8, §10.1 |
| 25 | Caching and OpenAI settings | AGT-3, AGT-5 |
| 27 | Demo page | DEMO-1, DEMO-2, API-6, AUTH-5 |
| 28 | Specs | TEST-1 to TEST-13 |
| 29 | Tool-call eval | EVAL-1 |
| 30 | LLM-judge eval (example) | EVAL-2 |
| 32 | One logging and tracing solution | OBS-1 to OBS-4, ENV-7 |
| 34 | Cursor paging and size contract | TOOL-5, TOOL-7 |
| 40 | Safety net | SAFE-1 to SAFE-3, CTX-1 step 5 |
| 44 | API contract spec | DOC-1 |
| 45 | Diagrams | DOC-2 |
| 46 | Mobile integration notes | DOC-3 |
| 47 | Privacy considerations | DOC-4 |
| 49 | Final summary | DOC-5 |

## Appendix A — TDD defaults to review

Details this document chose because the decisions left them open:

1. No `ingestion` dependency group and no PDF parser: MVP sources are
   Markdown curated by hand (ENV-3, ING-1).
2. Docker: official Python 3.14 slim base, `runtime` and `dev` targets,
   non-root user, port 8000; Compose services `init`, `capper`, `traces` and
   `dev`, and the `capper-data` volume at `/app/data`; `GET /healthz`
   (ENV-6 to ENV-9, API-15).
3. Content files in `content/source/` with `content/manifest.toml` (CNT-1).
4. A third `load` value, `app`, for documents the app reads but never sends
   to the chat model (DATA-9).
5. The safety-check prompt is a content document, and the check returns
   structured output validated against the policy names (CNT-1, SAFE-1).
6. `turns.request_text_hash` to detect a reused idempotency key, and
   `turns.app_version` for code-side prompt provenance (DATA-2, ING-5).
7. Feedback comments up to 500 characters (DATA-13).
8. The content-version formula over name, class, load and hash (DATA-15).
9. RS256 for tokens; the bootstrap creates the dev key pair; demo
   sessions last 60 minutes (AUTH-1, AUTH-5).
10. Tool limits: page size default 10, max 50; result cap 8,000 characters;
    short descriptions up to 200 characters; 1–10 IDs per card call;
    case-insensitive name and description matching; the list orders
    (TOOL-5, TOOL-7, §8.2).
11. `min_clear_tokens` of 2,000 (CMP-3).
12. The opaque user key is HMAC-SHA256 of the user ID with a configured
    secret, used as the cache key and the `conversation_id` (AGT-5).
13. Account context before the history and turn context before the turn's
    prompt, both request-only; a flagged policy as a system-role part of the
    turn context (CTX-1, CTX-2).
14. History endpoint `limit` default 20, max 100; `Idempotency-Key` is
    required (API-2, API-3).
15. Where message IDs appear in stream events (API-7).
16. The demo page renders a small Markdown subset (DEMO-2).
17. `otlp_endpoint` default (§13).
18. Starting values carried from the setup spike (history budget 20,000
    tokens, 10 tool calls per turn, 8,000-character messages, 4,096 output
    tokens, 5 s and 60 s timeouts), and `model_prices` estimates from the
    D-047 research (§13).
19. The `content_class` values `operator_policy` and `user_knowledge`
    (DATA-9).
20. On shutdown, wait up to the turn timeout, then cancel and mark `error`
    (API-10).
21. The tool-call limit's mechanics: tool use disabled on the next request,
    and a model-request backstop of the limit + 2 (TOOL-4).
22. The summary heading check as an output validator on the summarizer
    (CMP-5).
23. Stopped and errored turns close interrupted tool calls with a synthetic
    "not run" result in the stored model history (API-14).
24. The wording of tool error results and synthetic tool results (TOOL-4,
    §8.2, API-14): what each must say is the requirement; the exact strings
    are defaults.
25. The safety check's model settings: native structured output, reasoning
    off, a 200-token cap (SAFE-1). Measured: median 1.71 s → about 1.0 s.

## Appendix B — Build-time verifications

Library wiring to confirm while building. Each is resolved during the build
and recorded against its requirement. Only a failure that would force a
change to agreed behavior (a decision or a requirement's meaning) stops the
build and is raised with Sam.

1. **Capability order and composition** (AGT-7, CMP-4, CTX-2): that
   `ClearToolResults`, then `SummarizingCompaction`,
   then `ReportContextUsage`, then the request-only injector compose as
   described and run before each model request; and that a summarizing
   failure raises rather than being skipped.
2. **Capturing a compaction** (CMP-7): that a run's resulting history exposes
   the summary message and the suffix length, so the watermark can be
   computed by position, and that the run's new messages can be persisted
   unaffected by compaction.
3. **Heading validator** (CMP-5): how to attach an output validator to the
   Harness summarizer (for example through its summarization capabilities)
   so a missing heading is retried and then raises.
4. **Running from a stored prompt** (API-3, DATA-5): that a run can start
   from a history ending in the stored user prompt, so the prompt isn't
   duplicated in `model_messages`.
5. **Disabling tool use for one request** (TOOL-4): the Pydantic AI
   mechanism for tool choice `none` with unchanged definitions, and that
   `UsageLimits` ends the run as the backstop.
6. **Encrypted reasoning on GPT-6** (AGT-3): that the configured models'
   profiles support encrypted reasoning content, so `store: false` keeps
   reasoning within a tool-calling turn (D-087).
7. **Cancellation** (API-11): that stopping a streamed run keeps the
   interrupted state as D-046 describes in Pydantic AI 2.69.
8. **Instrumentation** (OBS-1): that `include_content=False` keeps all
   message content out of spans, including tool arguments and results.

## Appendix C — Not in the MVP (do not build)

Punted to `future-considerations.md` (D-078 onward): the confirmation flow
and any action tool needing approval (D-086); spilling oversized tool output
(D-088); dashboards; provider failover (D-061); rate limiting and spend caps
(D-077); CI; deployment and its design (D-085); REST list paging (D-080); the
memory-pressure warning (D-081); resumable streams (D-082); staged content and
upload triggers (D-083); conversation sessions (D-084); the privacy system
(purge, targeted redaction) (D-066); background consolidation of guidance
(D-068); learning user interests and collaborative filtering (D-070);
languages other than English (D-069); conflict resolution at ingestion beyond
hand curation (D-053); any use-case-specific tool, field, category or
feature (D-057).
