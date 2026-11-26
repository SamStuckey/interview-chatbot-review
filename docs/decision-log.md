# Decision Log

Append-only. Early decisions are not rewritten unless explicitly directed; a
reversal is recorded as a new entry that references the one it supersedes.

Status values: **Decided** (agreed, authoritative) · **Proposed** (on the table,
awaiting alignment) · **Open** (being settled now) · **Deferred** (parked in
`open-tasks.md`) · **Superseded**.

**File renames (2026-11-17):** `open-tasks.md` is now `mvp-plan.md`, and
`summary-notes.md` is now `future-considerations.md`. Entries written before
the rename keep the old names.

**Planning files retired (2026-11-19):** `mvp-plan.md` (with the TDD) is now
`checkpoints/00-mvp-design-spike.md`, and `post-mvp-cleanup.md` is
`checkpoints/05-post-mvp-cleanup-checklist.md`. `future-considerations.md` was
folded into `known-limitations.md`, which now holds deferred work. Entries
written before keep the old names.

## Entry format (from D-032 on)

Every new entry has the same fields:

- **Question:** what had to be decided.
- **Considered:** the options weighed, with their trade-offs.
- **Decision & rationale:** what we chose and why.
- **Status / supersedes:** current status and links to related entries.

Entries D-001 to D-031 predate this format and are left as written (append-only).
The index below shows the **current** status of every entry.

**Reading entries as build directives.** An entry's decision, as amended by
the later entries its index row points to, is the directive. Examples inside
entries (sample messages, products, health details, mockup quotes) illustrate
that decision or name a test fixture; they are not scope on their own
(D-057). Exact wording is required only where an entry says so.

## Index (current status)

| ID | Question → decision (one line) | Status |
|---|---|---|
| D-001 | Process → AI prototype, then Sam refactors by hand | Decided (Sam has permission to proceed this way, 2026-11-17; D-052 point 1 resolved) |
| D-002 | Focus area → context engineering | Decided |
| D-003 | Session log → verbatim log is a deliverable, appended every turn | Decided (our chosen supporting material, not a brief requirement → D-052) |
| D-004 | MVP knowledge → send all of it, no RAG | Decided (rationale → D-016; scope → D-031) |
| D-005 | Caching → most stable content first, cache breakpoints | Decided (principle stands; breakpoint mechanics superseded by D-048) |
| D-006 | Structured data → tools/queries, never embeddings | Decided |
| D-007 | No test switches in prod code; tests stub via DI | Decided (framework part reopened → D-041) Thin-client and no-LangChain parts superseded by D-044; the no-test-switch rule stands; its one exception, the demo sign-in → D-092. |
| D-008 | Seeds extend the mock DB | Decided (no domain-specific product attributes such as allergen/dietary tags → D-051, D-057; no categories → D-058) |
| D-009 | `user_id` only from auth context; all queries scoped | Decided |
| D-010 | Minimal chat page styled after mockups | Decided (refined by D-019) |
| D-011 | Action tools allowed with user confirmation | Decided (refined by D-026; MVP has no confirmed actions, flow designed only → D-054) |
| D-012 | Content change management | Superseded by D-016 |
| D-013 | LLM-as-judge used sparingly | Decided (refined by D-025) |
| D-014 | Memory & compaction design | Superseded in part: truncation fallback and N-message retention → D-043; code-enforced preferences → D-051 |
| D-015 | Exclude legacy history from context | Superseded by D-017 |
| D-016 | Canonical content pipeline; prompt follows docs | Decided (MVP filesystem bundle superseded by D-050: content table) |
| D-017 | Legacy history demonstrative; control user | Decided Control-user experiment retired and legacy table dropped → D-092. |
| D-018 | NDJSON typed-event streaming | Decided (cancellation clause superseded by D-046) Example event names superseded by D-063. |
| D-019 | Demo page = vanilla JS consuming NDJSON | Decided |
| D-020 | Stateless bearer tokens verified per request | Decided Demo sign-in (user list → session) → D-092. |
| D-021 | MVP LLM provider | Superseded by D-047 |
| D-022 | Adopt LangChain | Superseded by D-044 (Pydantic AI) |
| D-023 | One thread per user | Decided → D-036 |
| D-024 | Preference memory (typed tool + background) | Superseded by D-051 |
| D-025 | Evaluation strategy | Decided for the MVP → D-062 (principles stand) |
| D-026 | Human-in-the-loop rules | Decided (designed, not built for the MVP → D-054; T3) |
| D-027 | Seed user set | Decided (control user retired → D-092; seeds as built → TDD §5.5) |
| D-028 | Compaction parameters (N = 20, threshold) | Superseded in part by D-043 (retention now counted in tokens) |
| D-029 | Cache order correction (tools before system) | Superseded by D-048 (request assembly is the framework's) |
| D-030 | Mockups are spec, not LLM content | Decided |
| D-031 | Four-class content taxonomy | Decided → D-049 |
| D-032 | Ingestion in its own package; shared contract | Decided (contract now defines the content table, D-050) |
| D-033 | Application code is provider-agnostic | Decided |
| D-034 | Canonical assistant name: Capper | Decided |
| D-035 | Product-knowledge doc authored & ingested | Decided |
| D-036 | One thread per user (locked) | Decided (no server-side session boundaries → D-060) |
| D-037 | Preference memory accepted + tests required | Superseded by D-051 (test list adapted) |
| D-038 | Compaction: fill to N%, compact and replace | Decided (last-20-messages retention superseded by D-043) |
| D-039 | Caching layers & invalidation | Superseded by D-050 (provider mechanics → D-048) |
| D-040 | Uniform decision format | Decided |
| D-041 | Orchestration framework (research captured) | Decided → D-044 |
| D-042 | Reopen caching (D-039) and preference memory (D-024/D-037) | Decided (resolved by D-050, D-051) |
| D-043 | Context budget & compaction design (layered defenses) | Decided; MVP cut → D-064. Required evals revised by D-062: fact retention is written up only; oversized-input and retry cases become specs if built; page-1 case depends on T14 Mechanism → D-089 (Harness compaction). Summary format: fixed template with required headings, validated → D-091. |
| D-044 | Agent framework → Pydantic AI (Q1) | Decided |
| D-045 | Web framework & data layer → FastAPI, async SQLAlchemy + aiosqlite (Q7) | Decided |
| D-046 | Stop vs. disconnect; stopped turns kept (Q8) | Decided (resumable streams punted → D-082) Untargeted Stop superseded: Stop is bound to a turn → D-090. |
| D-047 | Provider & models → OpenAI; chat Terra, compaction Luna (Q2) | Decided (storage wording clarified → D-052) |
| D-048 | Provider caching mechanics belong to the framework (cleanup) | Decided |
| D-049 | MVP content set, taxonomy, do-no-harm policies (Q4) | Decided (demo referral conflicts → D-053; policy topics are content only → D-057; the safety-net check agent is built as a simple POC, mvp-plan #40) |
| D-050 | Content in a database table; caching (Q5) | Decided (cache-key wording clarified → D-052; production content pipeline punted → D-083) Content snapshot and publishing clarified → D-090. Content version formula and `app_version` → D-092. |
| D-051 | Preference memory → avoid list + guidance notes (Q6) | Decided (generic notes; domain categories excluded by design → D-057) |
| D-052 | Documentation clarifications (D-001, D-003, D-047, D-050) | Decided (point 1 resolved: Sam has permission, 2026-11-17) |
| D-053 | Demo referral conflicts → hand-curated, Rules win | Decided (example values → D-055) |
| D-054 | MVP action tools → no records created | Decided (no grocery-list feature → D-057; confirmation flow punted → D-086) |
| D-055 | Example values handled at ingestion, demo included | Decided |
| D-056 | Rich response parts → streamed text + typed cards from verified data (W1) | Decided |
| D-057 | Architectural boundary → generic capabilities, not use-case features | Decided Generalized to all examples by D-093. |
| D-058 | MVP tool set (W2) | Decided (purchase history tool added → D-059; popular-products fallback → D-070; history search → D-074) |
| D-059 | Purchase history → `get_my_purchases` lookup tool (W3) | Decided |
| D-060 | Greeting, sessions and time (W4) | Decided (conversation sessions punted → D-084) |
| D-061 | Provider failures → one generic error (W5) | Decided (provider failover punted in the 2026-11-17 sort, D-078) Retry and error channels clarified → D-090. |
| D-062 | Specs vs. evals → specs for deterministic parts; one tool-call eval (`read_document`); one LLM-judge eval (commented out) (W6) | Decided (D-043 evals resolved, Sam 2026-11-17) |
| D-063 | API contract (W7, T6) | Decided (feedback endpoint added → D-076) Duplicate-send responses, turn-bound Stop and error channels → D-090. |
| D-064 | MVP cut for D-043 → budgeting, compaction with background job, Harness, generous limits (W8, T14) | Decided (its "design only" items: cursor paging built → D-080; REST list paging punted → D-080; memory-pressure warning punted → D-081) Compaction mechanism → D-089; oversized output → D-088. |
| D-065 | Tool results verbatim → current turn all; last 5 from completed turns (W9) | Decided Whole-turn compaction clause superseded by D-089; retention wording → D-090. |
| D-066 | User-shared content handled generically; privacy system (purge, redaction) is a future consideration (W10) | Decided (per D-078) |
| D-067 | Conflicting guidance notes → newer supersede earlier (MVP) (W11) | Decided |
| D-068 | Guidance limits → 30 notes × 300 chars, normalized, optional expiry (W12) | Decided |
| D-069 | Language → English only for the MVP (W13) | Decided |
| D-070 | Users with little data → best effort; `get_popular_products` fallback (W14) | Decided "Near the user" corrected to "at your school"; aggregate-only, avoid list applied → D-090. |
| D-071 | Data model (T16) | Decided (history search index added → D-074; `message_feedback` → D-076) Watermark at the model-message level → D-090. |
| D-072 | System design: structure and request flow (T1) | Decided (compaction job → D-089) |
| D-073 | Confirmation flow (T3) | Decided as a design; punted to future considerations → D-086 |
| D-074 | History search → `search_my_history`, SQLite FTS5 (T5) | Decided Bounded top-5 lookup, exempt from the cursor contract → D-090. |
| D-075 | Observability (T7) | Decided (mechanism superseded by D-079: one OpenTelemetry trace solution, built; dashboards punted) |
| D-076 | User feedback → thumbs up/down + comment, built in the MVP (T8) | Decided |
| D-077 | Security audit of the design; five gaps (T13) | Decided (`pip-audit` and safe Markdown built; spend limits and CI punted in the 2026-11-17 sort) |
| D-078 | Scope model: one app, two buckets (MVP, future considerations), Dockerized | Decided |
| D-079 | One observability solution: OpenTelemetry traces in a local viewer container (Q1) | Decided |
| D-080 | Cursor paging on list tools; REST list paging punted (Q2) | Decided Deterministic list orders → D-092. |
| D-081 | Memory-pressure warning and pre-compaction extraction punted (Q3) | Decided |
| D-082 | Resumable streams punted (Q4) | Decided |
| D-083 | Production content pipeline punted (Q5) | Decided |
| D-084 | Conversation sessions punted; login sessions stay with the identity provider (Q6) | Decided |
| D-085 | Deployment design document punted, merged into the deployment note (Q7) | Decided |
| D-086 | Confirmation flow punted (no MVP tool needs approval) | Decided |
| D-087 | Build-time checks settled from the installed source (Harness clearing config, store false, API names) | Decided Retention wording → D-090. |
| D-088 | Oversized tool output: limits in our tools; Harness spill punted (Q-A) | Decided |
| D-089 | Compaction built on the Harness (tiers, background start, our persistence) (Q-B) | Decided Watermark and thresholds clarified → D-090. Summary format → D-091. Summarizer settings, per-user `conversation_id`, no `skip_on` → D-092. |
| D-090 | Contract reconciliation after the documentation review (compaction boundary, send/stop/errors, safety ordering, catalog, search, content snapshot) | Decided Watermark by position, turn outcomes, request-only context → D-092. |
| D-091 | Compaction summary format: Harness summarizer, fixed template with required headings, checked before saving | Decided Heading check placed as a summarizer output validator → D-092. |
| D-092 | TDD review reconciliation (request-only context, compaction by position, turn outcomes, clean-checkout sequence) | Decided; walkthrough with Sam recorded in the entry (demo sign-in exception, control user and legacy table dropped); first-run sequence superseded → D-094 |
| D-093 | Requirements, defaults and examples kept distinct (standing rule) | Decided |
| D-094 | A fully Dockerized product: named volume, init service, health check | Decided |
| D-095 | Interrupted tool calls are closed by the framework, not in stored history | Decided; supersedes D-092's synthetic "not run" result |
| D-096 | Compaction runs inline; the background start is removed | Decided; supersedes D-089 item 2 |
| D-097 | Post-MVP cleanup: the implementation choices | Decided; supersedes D-090's safety check and D-051's avoid list in context |
| D-098 | Simplify Alembic to one initial migration and direct execution | Decided; supersedes D-097's separate time-zone migration |

---

## D-001 — Build process: AI-assisted prototype, then manual refactor
- **Date:** 2026-11-16
- **Status:** Decided (Sam)
- **Decision:** Use the AI pair to reach a working prototype quickly. Sam then
  manually refactors all submitted code for clarity and cohesion so that the
  submitted code is his own, per the challenge's prohibition on generative-AI
  code.
- **Implication:** Favor small, legible modules and a minimal dependency
  surface — every line will be hand-reworked, so abstraction weight is a cost.

## D-002 — Focus area: context engineering
- **Date:** 2026-11-16
- **Status:** Decided (Sam)
- **Decision:** The "area that interests us" is context engineering. The
  prototype may be relatively simple, but the spec will design the full,
  production-grade context system (retrieval, memory, tool use, guardrails,
  evals).

## D-003 — Session conversation log is a deliverable
- **Date:** 2026-11-16
- **Status:** Decided (Sam)
- **Decision:** Submit a conversation log of this session. Sam's input is
  verbatim (formatting fixes only); assistant output verbatim minus
  thinking/tool spew. Mechanism (manual append vs. transcript export) — open.

---

## Facts established from the supporting files (2026-11-16)

Not decisions — recorded here because several upcoming decisions depend on them.

- **Knowledge base is tiny.** Referral FAQ + Program Rules ≈ 1.5k tokens
  total; product catalog is 10 rows. The whole corpus fits in a single prompt.
- **The two KB docs disagree.** FAQ: bonus after onboarding *and* linking a
  school; must use the link. Rules: onboarding *and* a qualifying action (scan
  *or* link school); code usable within a window (e.g. 48h). Rules also use
  "e.g." placeholder values ($5) that must not be stated as fact.
- **`Purchase_History` is empty.** Personalization-from-purchases is not
  possible with the provided data as-is.
- **`Conversation_History` has no conversation/session id** — a flat per-user
  message log. All 484 rows are off-topic chit-chat (jokes, trivia, homework
  help), i.e. an example of a bot *not* aligned with its purpose.
- **Mockups reference data the DB doesn't have:** per-user referral code
  (`XY7G4D`), "Bonus Caps" promotions, product cards with images, products not
  in the catalog (tortillas, sour cream, yogurt...), dietary attributes.
- **Mockups imply API requirements:** persona "Capper" with a fixed greeting;
  "processing" state with a stop button (→ streaming + cancellation); product
  card carousel and formatted step lists (→ structured response parts, not a
  bare string); "I'll direct you to someone who can" (→ human handoff path).

- **KB gap surfaced by the mockups:** the referral mockup tells the friend to
  enter the code "on the Complete Profile step". Neither KB document mentions
  this. The bot can only say it if it's added to the knowledge content, or it
  is a hallucination.
- **Legacy `Conversation_History` is synthetic:** 20 fixed user prompts, each
  mapped 1:1 to a fixed bot reply; reply gaps are always 3–6s; all 34 users
  fall within one 2-hour window on 2025-04-03; the bot calls itself "ChatPal"
  (not "Capper"). Zero rows mention referrals or products.
- **All app data is in the provided DB** (Users, Schools, Products,
  Purchase_History, Conversation_History). The existing REST API covers only
  authentication and registration.

---

## D-004 — MVP knowledge retrieval: include-all, RAG as considered alternative
- **Date:** 2026-11-16
- **Status:** Decided
- **Decision:** For the MVP, the full knowledge base (referral FAQ, program
  rules, voice/persona) is placed in the cached system context on every
  request. No chunking, embedding or re-ranking.
- **Considered alternative:** hybrid retrieval (BM25/FTS + embeddings,
  re-ranker, top-k into context) behind the same knowledge-source interface.
- **Trade-off:** retrieval adds infrastructure (vector store, embedding model,
  ingestion pipeline, re-index on change), more ways to fail (recall misses),
  and evals of its own. At ~1.2k tokens (estimate) of content it buys nothing.
  Switch point: once the KB is too large to send every time, or once
  irrelevant content measurably hurts answer quality.

## D-005 — Prompt caching, with the context ordered from most to least stable
- **Date:** 2026-11-16
- **Status:** Decided
- **Decision:** Order the context so the most stable content comes first
  (persona/policy → knowledge → tool definitions → per-user profile →
  memory/summary → recent turns), and put cache breakpoints after the stable
  layers. Caching works on a prefix, so anything that changes per user or per
  turn must come after the cached part.
- **Rationale:** cuts cost and latency on every turn. It also gives a simple
  rule for KB changes: a content change changes the prefix, so the cache
  invalidates itself.

## D-006 — Structured data goes through tools/queries, never embeddings
- **Date:** 2026-11-16
- **Status:** Decided
- **Decision:** Products, promotions, user profile, referral codes and purchases
  are read with typed queries, exposed to the model as tools or loaded
  deterministically. Embeddings are reserved for unstructured text (large KB,
  verbatim conversation recall).
- **Guarantee:** product IDs in model output are checked against the catalog
  after generation; unknown IDs are rejected.

## D-007 — LLM integration: a thin client we own; tests stub it; no test modes
- **Date:** 2026-11-16
- **Status:** Decided (Sam — authoritative)
- **Decision:** Production code depends on a small LLM client interface with
  exactly one real provider implementation. **Production code contains no
  mock/fake/test mode, flag or switch.** Tests replace the client through
  dependency injection inside the test suite only.
- **LangChain/similar:** not used for the MVP: it adds abstraction we'd have to
  rewrite by hand and hides the context work. **Trade-off noted:** a wrapper
  like this becomes worthwhile if the customer plans to compare several LLM
  providers, or to migrate to a self-hosted/proprietary model.

## D-008 — Seed data extends the mock DB
- **Date:** 2026-11-16
- **Status:** Decided
- **Decision:** Build seeds that supply what the mockups need and the DB lacks:
  purchase history, per-user referral codes, Bonus Caps promotions, product
  attributes (category, dietary/allergen tags, participating flag), and
  products shown in the mockups.
- **Rationale:** the brief says to "use user information", which needs data;
  and the seeds must support tests showing that one account **cannot** access
  another's data.

## D-009 — User-scoped access enforced in the application layer
- **Date:** 2026-11-16
- **Status:** Decided
- **Decision:** `user_id` comes only from the authenticated request context.
  It is never a tool argument the model can supply or override. Every query
  for user-owned data (conversations, messages, memory, purchases, referral
  code) is scoped by it in the data-access layer. Foreign keys provide
  integrity, not authorization; the app enforces authorization.
- **Tests:** cross-account access tests are required (see D-008).

## D-010 — Chat UI: minimal page, styled after the mockups, no dependencies
- **Date:** 2026-11-16
- **Status:** Decided (Sam); JS scope open (see P-005)
- **Decision:** Build a simple chat page styled after the mockups. No
  libraries, no build step, as little code as possible. If refactoring it by
  hand proves too costly, it is flagged in the submission as an
  AI-generated illustrative extra outside the requirements.
- **Rationale:** the product is a mobile-app integration; a visible chat
  surface shows the API contract working end to end.

## D-011 — Action tools allowed, with human-in-the-loop confirmation
- **Date:** 2026-11-16
- **Status:** Decided (Sam)
- **Decision:** Design to the mockups: the agent may use action tools (e.g.
  build a grocery list, hand off to support). Any action that creates or
  destroys something requires explicit user confirmation. Pattern: the model
  *proposes* an action → the API returns a pending-action part → the client
  confirms → the server runs the **validated, stored** arguments (the model
  does not regenerate them). Read-only tools run without confirmation.

## D-012 — Knowledge/voice content change management
- **Date:** 2026-11-16
- **Status:** Decided (MVP) / Designed (production)
- **MVP:** knowledge and voice content live as versioned files in the repo;
  changing them means a commit that passes the eval suite.
- **Production design (not built):** content is published to object storage
  (e.g. S3) through a simple admin workflow; the app fetches and caches it,
  keyed by version/ETag; every assistant message records the content version
  it was generated with (for tracing); a new version must pass evals before
  promotion. Prompt-cache invalidation happens automatically (D-005).

## D-013 — LLM-as-judge used sparingly
- **Date:** 2026-11-16
- **Status:** Decided (Sam)
- **Decision:** Deterministic checks and unit/integration tests first.
  LLM-as-judge is reserved for qualities that can't be tested
  deterministically (tone, being on-purpose), run on a sampled or offline
  golden set against a written rubric, with cost tracked. Designed; build
  unlikely for the MVP.

## D-014 — Conversation memory & compaction
- **Date:** 2026-11-16
- **Status:** Proposed (Sam's design + refinements); build scope decided at build time
- **Design:**
  - Verbatim history is stored permanently and **never rewritten**; the
    transcript the user sees is always verbatim. Compaction changes only what
    the model sees.
  - Model context = latest summary + every message after the summary's
    watermark (`covers_through_message_id`), always including the N most
    recent messages verbatim.
  - When the unsummarized messages exceed a token threshold T, an async job
    summarizes the oldest slice and writes a *new* summary row with a new
    watermark in one atomic step. Readers always see a consistent (summary,
    watermark) pair, so there is no downtime. If the job lags, a hard token
    cap truncates as a fallback.
  - Preferences ("never offer X again", allergies, likes) are extracted into a
    **structured** user-level store, not left in prose summaries, and are
    enforced **in code** (e.g. the product tool filters excluded items), not
    only through the prompt.
  - A recall tool `search_history(query)` is scoped to the authenticated user.
    MVP option: SQLite FTS5 (built in, no new dependency); later: embeddings.

## D-015 — Legacy `Conversation_History` is excluded from model context
- **Date:** 2026-11-16
- **Status:** Proposed
- **Decision:** Do not load legacy rows into model context. They come from an
  off-persona bot ("ChatPal") answering trivia and homework; feeding them in
  would teach the model the wrong persona and scope. Reuse the 20 distinct
  user prompts as an off-topic/small-talk **eval set**. Migration: archive or
  drop when the new conversation schema lands.

---

## Mockup-implied requirements

Source: `supporting-files/Livefront Engineering Challenge UI Design (AI).pdf`.
(Note, D-057: these are behaviors to support through generic capabilities; the
food details are examples, not features.)
PR = product recommendation flow (pp. 3–4); RF = referral flow (pp. 6–7).

| ID | Requirement | Evidence in mockup |
|---|---|---|
| R-01 | Persona "Capper", a personal Carton Caps assistant; screen titled "Personal Assistant" | Greeting: "Hi! I'm Capper, your personal Carton Caps assistant." (PR, RF) |
| R-02 | A fixed 3-bubble greeting when a conversation opens | Same three greeting bubbles in every state screen (pp. 4, 7) |
| R-03 | Hand-off to a human/support when the bot can't help | "If there's anything I can't help you with, I'll direct you to someone who can." |
| R-04 | Ask clarifying questions before recommending when information is missing | PR: asks about allergies and likes/dislikes before recommending |
| R-05 | Gather constraints across turns and apply them | PR: "no veggies, no sauces, and no spices" pulled from the user's free text |
| R-06 | Recommend only participating Carton Caps products | PR: "Here are some participating Carton Caps products…" |
| R-07 | Allergy-aware: ask about allergens; don't claim products are safe beyond the data | PR: "Any food allergies or sensitivities… Nuts, dairy, gluten?" |
| R-08 | Offer a follow-up action and respect a "no" | PR: "Would you like me to help you build a grocery list?" → "No, that's okay." |
| R-09 | Current promotions, tailored to the conversation | PR: "Bonus Caps… especially for picky eaters" |
| R-10 | Rich response parts: lists, card carousel (image + title), section header | PR: "This Week's Bonus Caps" cards ("Earn 5 extra Caps on Mac & Cheese") |
| R-11 | Several short bubbles per turn → a response is an ordered list of parts | Every bot turn renders as 2–4 bubbles |
| R-12 | Processing state with a stop control → streaming/async + cancellation | "Chatbot Processing" screen: typing dots, send becomes a stop button |
| R-13 | Conversation start timestamp | "Today, 1:43pm" header |
| R-14 | Diagnose before instructing | RF: "What are you having trouble with when referring Sally?" |
| R-15 | Adapt to the situation | RF: in person at a PTO meeting → share the code rather than a link |
| R-16 | Personal data: the user's own referral code | RF: "your personal referral code: **XY7G4D**" |
| R-17 | Step-by-step instructions with headings | RF: Download app / Create account / Enter referral code / Scan first receipt |
| R-18 | Instructions grounded in the KB. The "Complete Profile" step is **dropped** (D-035) | RF step 3 |
| R-19 | Recall earlier context in the sign-off | RF: "Have a great PTO meeting!" |
| R-20 | Polite close: "anything else?" then a goodbye | Both flows |
| R-21 | Third-party personal data (friend's name) handled with care | RF: "Sally" is used throughout |
| R-22 | Bonus condition shown matches the Rules (scan qualifies), not the FAQ | RF: "When she does [scans], you'll both earn Bonus Caps" |

---

## D-016 — Canonical content pipeline; the prompt follows the documents
- **Date:** 2026-11-16
- **Status:** Decided (Sam)
- **Supersedes:** D-004's switch-point rationale ("once irrelevant content
  measurably hurts…"), and D-012 (merged here).
- **Decision:** The customer's documents are the single source of truth.
  The prompt is derived from them, never edited independently. Pipeline:
  `source docs → ingestion (PDF → normalized text) → versioned content bundle
  (content hash) → deterministic prompt render → provider prompt cache`.
  When a document changes, its hash changes, the rendered prefix changes, and
  the cache is rebuilt automatically. This is **not RAG**: nothing is
  retrieved or ranked; the full text is sent.
- **MVP:** source docs committed under `content/source/`. An ingestion
  script (outside the service) writes `content/bundle/` plus a manifest with
  hashes. The service loads the bundle at startup.
- **Production design:** documents published to object storage (e.g. S3) →
  an upload event triggers the ingestion job → a new versioned bundle →
  instances swap it in atomically → every assistant message records the bundle
  version. A new bundle passes the eval suite before promotion.
- **Rationale:** irrelevant or conflicting context always costs quality
  (Chroma's "context rot" study found similar-but-wrong *distractors* the most
  damaging). Keeping content in lock step with the canonical docs avoids
  needing to measure drift that the system can't observe.
- **Option noted:** ingestion-time redaction of "e.g." placeholder values
  (see summary-notes.md).

## D-017 — Legacy chat history is demonstrative only; we seed our own
- **Date:** 2026-11-16
- **Status:** Decided (Sam)
- **Supersedes:** D-015.
- **Decision:** Treat `Conversation_History` as an example of the history's
  shape, not as real data. Seed users get histories we design. One **control
  user** keeps the legacy "ChatPal" history so we can observe how the model
  behaves when off-persona history is present. Not raised with the
  interviewer.

## D-018 — Streaming responses as NDJSON typed events
- **Date:** 2026-11-16
- **Status:** Decided (Sam)
- **Decision:** The message endpoint streams `application/x-ndjson`; each line
  is a typed event (e.g. `message.start`, `text.delta`, `part` (list / card
  carousel / pending action), `message.end`, `error`). Matches the mockups:
  multi-bubble turns, rich parts, processing state (R-10, R-11, R-12).
  Cancellation: the client aborts → the server cancels the upstream LLM stream
  → the partial message is stored and marked `interrupted`.

## D-019 — Demo chat page: vanilla JS consuming the NDJSON stream
- **Date:** 2026-11-16
- **Status:** Decided (Sam)
- **Resolves:** P-005.
- **Decision:** The real client is a mobile app, so the demo page acts like
  one: a static page with plain JS (`fetch` + stream reader) that calls the
  JSON/NDJSON API and renders parts. Styled after the mockups. No server-side
  rendering, no libraries.

## D-020 — Auth model: stateless bearer tokens verified per request
- **Date:** 2026-11-16
- **Status:** Decided
- **Decision:** The existing auth API is the identity provider. It issues a
  short-lived signed access token (JWT) plus a refresh token at login; the
  mobile app sends `Authorization: Bearer …` on every call. The chat service
  is a *resource server*: it verifies signature, `exp`, `iss` and `aud` locally
  on each request (public keys, no call to the auth API) and takes `sub` as
  `user_id`. There is no server-side session for the chat service to manage.
- **MVP:** the same verification path, with a dev signing key from config. A
  dev script (outside the service) mints tokens for seed users; tests mint
  tokens in fixtures.
- **Edge cases to test:** missing/malformed token, bad signature, `alg`
  confusion/`none`, expired, wrong `iss`/`aud`, a valid token for a user not
  in the DB, and cross-account access.
- **Trade-off noted:** reading the app's `Users` table directly couples us to
  their schema. In production, prefer a profile API or a read-only view.

## D-021 — LLM provider for the MVP
- **Date:** 2026-11-16
- **Status:** Proposed
- **Decision:** Anthropic or OpenAI (Sam supplies the key). Recommendation:
  Anthropic, for its explicit `cache_control` breakpoints. Caching is then
  deterministic and testable via `usage.cache_read_input_tokens`; OpenAI's
  automatic caching has reported intermittent misses. (Disclosure: this
  recommendation comes from a Claude model.) The model tier is Sam's call.

## D-022 — Revisit LangChain: adopt v1 `create_agent` + middleware
- **Date:** 2026-11-16
- **Status:** Proposed — would supersede the "LangChain not used" part of
  D-007. D-007's no-test-switch rule stands either way.
- **What it provides that we'd otherwise build:** provider abstraction; the
  agent/tool loop; `SummarizationMiddleware` (token/message trigger, `keep`
  defaults to 20 messages); `HumanInTheLoopMiddleware`
  (approve/edit/reject, per tool); PII detection/redaction; model-call and
  tool-call limits; model/tool retry; model fallback; an Anthropic
  provider-specific middleware; checkpointers (SQLite/Postgres) keyed by
  `thread_id`.
- **What we still own:** the content bundle and system prompt; per-user
  context and preference memory (as custom middleware); auth-scoped tools; our
  own verbatim message store (the checkpointer's state is the model's view
  and gets summarized; our table is the user's record); NDJSON event mapping.
- **Costs:** a large dependency with a history of API churn; abstraction
  makes debugging harder; it adds a second store of conversation state; and
  the summarization middleware appears to run inline before the model call,
  not asynchronously (to verify).
- **Why reconsider:** less hand-written code to refactor, and standard,
  recognizable patterns for exactly the parts we were about to build by hand.
  Also gives provider portability (the original argument for a wrapper).

## D-023 — Conversation model: one continuous thread per user
- **Date:** 2026-11-16
- **Status:** Proposed (Sam's position; research supports it)
- **Resolves:** P-006 if accepted.
- **Decision:** No user-facing `conversation_id`. The API is scoped to the
  authenticated user (`/v1/conversation` and `/v1/conversation/messages`).
  "Creating" a conversation means get-or-create on first use. Session
  boundaries (time gaps) are recorded for greetings, the "Today, 1:43pm"
  header, and metrics, but they are not separate conversations.
- **Rationale:** the mockups show no conversation list or "new chat"; one
  thread per user is the common recommendation for assistant products; with
  no IDs in URLs there is no ID to tamper with, so cross-account access is
  impossible by construction. Topic bleed (the main argument for separate
  conversations) is handled by compaction + structured memory (D-014, D-024).

## D-024 — Preference memory: typed tool now, background extraction later
- **Date:** 2026-11-16
- **Status:** Proposed
- **Design:**
  - **Hot path (MVP):** a `remember_preference` tool with a small typed schema:
    `kind ∈ {avoid_product, allergy, dietary, like, other}`, optional
    `product_id`, and `note` free text. The model maps the user's words to the
    schema. Anything that doesn't fit goes to `other`.
  - **Background (designed):** after a session, or alongside compaction, an
    extraction pass proposes ADD / UPDATE / DELETE operations to the store.
    This catches what the hot path missed, merges duplicates and resolves
    contradictions. (LangMem / mem0 pattern.)
  - **Enforcement tiers:**
    - *Hard* (in code) only where a preference maps to data: `avoid_product`
      filters product tool results; `allergy` filters by allergen tags when
      present.
    - *Soft* for everything else: injected into the memory layer of the
      context.
  - **Brittleness controls:** the bot confirms what it remembered; users can
    view and delete memories; extraction cases are part of the eval set.

## D-025 — Evaluation strategy (Huyen / Husain best practice)
- **Date:** 2026-11-16
- **Status:** Proposed; refines D-013
- **Approach:**
  1. **Define criteria before building** (evaluation-driven development).
     Our criteria come from R-01..R-22 plus grounding, scope and safety.
  2. **Evaluate each component and the whole system:** content
     ingestion, context assembly, tool selection/arguments, output
     validation, and per-turn and per-conversation (task) outcomes.
  3. **Prefer deterministic checks** (exact match, schema validation, ID
     grounding, required tool called) wherever possible.
  4. **LLM-as-judge only for qualities that can't be checked
     deterministically** (on-purpose, on-voice). Use one judge per failure
     mode, with a binary pass/fail verdict, and validate it against human labels
     (agreement / TPR / TNR) before trusting it. The main risk is an
     unvalidated judge, more than cost; known biases are position, verbosity
     and self-preference.
  5. **Error analysis on real traces drives new evals**, once traffic
     exists. Golden conversations (the two mockup flows, plus legacy prompts as
     off-topic cases) cover the MVP.

## D-026 — Human-in-the-loop best practice (refines D-011)
- **Date:** 2026-11-16
- **Status:** Decided (research-backed)
- **Basis:** OWASP LLM Top 10 2025, LLM06 Excessive Agency (least
  functionality, least privilege, human approval for high-impact actions,
  authorization enforced downstream, audit logging). The OpenAI Agents SDK
  (`needs_approval` → interruptions + resumable state) and LangChain
  (`HumanInTheLoopMiddleware`: approve/edit/reject) implement the same pattern.
- **Our rules:**
  - pending actions are bound to stored, validated arguments, single-use, and
    expiring;
  - a decline returns to the model as a tool result, so the conversation
    continues gracefully;
  - every proposal and decision is audit-logged;
  - approval is treated as a UX gate, not a security control.

## D-027 — Seed user set: happy path first, edges catalogued
- **Date:** 2026-11-16
- **Status:** Decided (Sam)
- **Initial seeds (happy path):**
  - an established user with a school, purchases and a referral code;
  - a new user with no purchases;
  - a user with stated preferences and an allergy;
  - two users with parallel data for cross-account tests;
  - the control user with legacy history (D-017).
- **Catalogued, not seeded yet:**
  - no school linked;
  - referral already used or ineligible;
  - adversarial / prompt injection;
  - cross-account probing via tool arguments;
  - third-party PII in messages;
  - deactivated user holding a valid token;
  - non-US user;
  - child user (COPPA; ignored, see summary-notes.md).

## D-028 — Compaction parameters confirmed
- **Date:** 2026-11-16
- **Status:** Decided (Sam), one open sub-choice
- **Decision:** Keep the N = 20 most recent messages verbatim (this is
  also LangChain's default `keep`). Older history is summarized
  when the token threshold is crossed: **triggered by the threshold, not
  re-summarized on every request**. Per-request re-summarization would add an
  LLM call to every turn and break the message cache on every turn. Verbatim
  lookup tool (`search_history`): full-text and/or semantic, designed, MVP
  optional. Jobs retry with logging; falls back to token truncation.
- **Open (P-009):** summarize inline at the threshold turn (the standard
  pattern in LangChain's middleware and Anthropic's server-side compaction;
  one slower turn) vs. Sam's async watermark design (no added latency; more
  machinery).

## D-029 — Correction to D-005's ordering (provider render order)
- **Date:** 2026-11-16
- **Status:** Decided
- **Correction:** On the Anthropic API, `tools` render *before* `system`, so
  the cached prefix is `tools → system (persona/policy → content bundle)`,
  followed by per-user context and then the conversation. D-005 listed tools
  after knowledge. The principle (most stable first) is unchanged.

## D-030 — UI mockups are product spec, not LLM content
- **Date:** 2026-11-16
- **Status:** Decided (Sam)
- **Decision:** The mockups never go into the content bundle. They are the
  source of requirements (R-01..R-22) and eval cases only. Facts the bot states
  must come from canonical documents or tools. Where a mockup shows something
  no document supports (the "Capper" persona, the "Complete Profile" step),
  that marks a missing canonical document; the mockup can't fill the gap.

## D-031 — Content taxonomy: four classes of context, routed differently
- **Date:** 2026-11-16
- **Status:** Proposed
- **Correction:** The FAQ and Rules were treated as the whole knowledge base
  (D-004's "~1.2k tokens, fits in one prompt"). They aren't: they're
  user-facing answers that imply several documents we weren't given (list in
  summary-notes.md).
- **Classes:**
  1. **Operator policy** (governs behavior): purpose/scope charter, persona
     and voice guide, safety and escalation rules. Always in the cached system
     layer. Authored by us as stubs and flagged.
  2. **User-facing knowledge** (answers questions): FAQ, program rules, how
     Caps work, help/navigation, terms, privacy. Goes in the bundle; sent in
     full or loaded just-in-time by a tool, depending on size.
  3. **Live data** (changes often, per user): current bonuses, promotions,
     catalog, referral status. Tools only, never documents.
  4. **Internal-only** (must never reach the model): fraud-detection rules,
     abuse thresholds, internal support playbooks. Excluded by the ingestion
     manifest.
- **Open tension (P-012):** terms of service, privacy policy and a help center
  could push the bundle from ~1k to tens of thousands of tokens. Sending all of
  it on every turn conflicts with D-016's "irrelevant context always hurts".
  The likely answer is a just-in-time `lookup_document(topic)` tool for
  class-2 long documents, while class-1 stays always loaded. Not RAG unless
  the documents grow large enough to need ranking.

---

## D-032 — Ingestion lives in its own package
- **Question:** Where does ingestion code live, and how does it relate to
  the service?
- **Considered:**
  1. Ingestion inside the service, at startup. Simple, but it couples PDF
     parsing dependencies to the runtime and blurs responsibilities.
  2. A separate package with its own copy of the bundle format. Clean
     separation, but the format is duplicated and can drift.
  3. A separate package plus one shared contract module.
- **Decision & rationale:** Option 3. Layout:
  - `ingestion/` is a standalone package: source loaders, normalizers, and a
    bundle writer.
  - `content_bundle/` is the shared contract: manifest schema, hashing, and
    loader. Ingestion writes through it; the service reads through it.
  - Dependency direction: ingestion → shared; service → shared. The service
    never imports ingestion, and ingestion never imports service internals.

  Reuse without replication; ingestion-only libraries (e.g. `pypdf`) never
  enter the service.
- **Status:** Decided (Sam). Refines D-016.

## D-033 — Application code is provider-agnostic
- **Question:** How much does the application know about which LLM it uses?
- **Considered:**
  1. Call one provider's SDK directly. Simplest, but provider details spread
     through the code.
  2. An abstraction where application code names no provider or model.
- **Decision & rationale:** Option 2. The provider and model are chosen by
  configuration at the composition root. Provider-specific features (e.g.
  Anthropic `cache_control` breakpoints) live only inside the provider
  adapter. Prompts don't name the model either. This keeps a provider switch
  or a move to a self-hosted model a config change. How we implement the
  abstraction is D-041.
- **Status:** Decided (Sam).

## D-034 — Canonical assistant name: "Capper"
- **Question:** What is the assistant called?
- **Considered:** "Capper" (the mockups); a neutral name.
- **Decision & rationale:** "Capper". It's established in the product design.
  Recorded in the authored persona/voice document (a class-1 operator policy
  document), since mockups aren't LLM content (D-030).
- **Status:** Decided (Sam).

## D-035 — Product-knowledge document, authored and ingested
- **Question:** How does Capper know the app behaviors the mockup flows rely
  on (referral page, Bonus Caps, scanning receipts, linking schools)?
- **Considered:**
  1. Leave them out. The bot then omits or hallucinates them (R-18).
  2. Hard-code them in the system prompt. That bypasses the content pipeline.
  3. Author a product-knowledge document and ingest it like the others.
- **Decision & rationale:** Option 3. One canonical source, the same
  pipeline, and it's swappable when the customer provides real help content.
  Scope: only what the demo flows need. Sign-up screens and the rest of the
  app are out of scope (R-18's "Complete Profile" step is dropped). Clearly
  flagged as authored by us. The interviewer is asked about other product
  behaviors.
- **Status:** Decided (Sam).

## D-036 — One continuous thread per user (locks D-023)
- **Question:** Do users have one conversation or many?
- **Considered:**
  1. A `conversation_id` per conversation: clean topic boundaries and
     per-conversation metrics, but nothing in the mockups shows multiple
     conversations, and IDs in URLs are an attack surface.
  2. One thread per user: matches the mockups, needs no IDs, and is the
     common in-app assistant pattern.
- **Decision & rationale:** Option 2. The API is scoped to the authenticated
  user; get-or-create on first use. Session boundaries (time gaps) are
  recorded for the greeting, the timestamp header and metrics. Topic bleed is
  handled by compaction plus structured memory.
- **Status:** Decided (Sam). Supersedes D-023's Proposed status.

## D-037 — Preference memory accepted, with required tests
- **Question:** Do we adopt D-024's preference design?
- **Considered:** prompt-only memory (brittle, unenforceable); fixed rules
  per phrasing (brittle); a typed tool plus hard enforcement where data
  allows (D-024).
- **Decision & rationale:** Adopt D-024. Required tests for
  `remember_preference`:
  1. Schema validation (bad `kind`, unknown `product_id`).
  2. Scoping: writes only under the authenticated user; no `user_id`
     parameter exists.
  3. Enforcement: product search excludes avoided products.
  4. Duplicate and contradicting preferences.
  5. Delete/update.
  6. Eval cases mapping phrasings to expected calls.
- **Status:** Decided (Sam).

## D-038 — Compaction trigger: fill to N%, compact and replace
- **Question:** When does compaction run?
- **Considered:** on every request (rejected: an extra LLM call each turn and
  no caching); at a threshold (standard).
- **Decision & rationale:** At a threshold. When history reaches N% of its
  token budget, summarize everything older than the last 20 messages, and
  replace those messages with the summary in the model's view. The verbatim
  store is untouched. Confirms D-028. (An earlier reply wrongly suggested
  per-request compaction was on the table; it never was.) Inline vs.
  background execution is Q3.
- **Status:** Decided (Sam).

## D-039 — Caching layers & invalidation
- **Question:** Where and how is anything cached?
- **Considered:** an app-level shared cache (Redis) vs. in-process plus
  provider caching.
- **Decision & rationale:** Three layers; no Redis for the MVP.
  1. **Bundle storage (built artifact):** `content/bundle/` in the repo for
     the MVP; versioned S3 objects in production. Rebuilt only when a source
     document changes.
  2. **In-process (each service instance):** at startup, load the bundle and
     render the cacheable prefix (tools + system) once into an immutable
     object keyed by the bundle hash. Every request reuses the same bytes.
     Rendering is deterministic, so all instances produce identical bytes. In
     production, a new bundle (S3 event or ETag poll) is swapped in
     atomically; in-flight requests finish on the old version.
  3. **Provider prompt cache (on the LLM provider's servers):** keyed by the
     exact prefix bytes. We control only byte stability and breakpoint
     placement. One breakpoint goes after the system block, and the
     conversation tail is cached automatically. The shared prefix has no user
     data, so every user's request warms it for everyone. The 5-minute TTL is
     refreshed on each hit.
  - **Invalidation:** document change → new bundle hash → new prefix bytes →
    one provider cache miss and write → warm again. Optional pre-warm
    request on swap.
  - **Per-user data** (profile, summary, recent turns) sits after the
    breakpoint. It is read from the DB each turn (cheap); there is no
    app-side user cache for the MVP.
- **Status:** Decided. Refines D-005, D-016, D-029.

## D-040 — Uniform decision format
- **Question:** How do we record decisions consistently?
- **Considered:** free-form entries (what D-001 to D-031 used) vs. a fixed
  template.
- **Decision & rationale:** Fixed template (Question / Considered /
  Decision & rationale / Status), plus an index of current status at the top.
  Older entries stay as written (append-only); the index carries their
  current status.
- **Status:** Decided (Sam).

## D-041 — Orchestration framework
- **Question:** What implements the LLM abstraction (D-033), the tool loop,
  user confirmation (D-026), compaction (D-038), streaming (D-018) and
  auth-scoped tools (D-009)?
- **Considered:**
  1. **Our own thin adapter over the provider SDKs.**
     - For: full control and transparency. Anthropic's "Building effective
       agents" advises starting with the APIs directly.
     - Against: we build the loop, user confirmation, compaction and two
       provider adapters ourselves. That's the most code for Sam to refactor.
  2. **LiteLLM + our own loop.**
     - For: provider abstraction solved.
     - Against: it's a gateway, not an agent framework; we still build the
       loop, confirmation and compaction.
  3. **LangChain v1 (`create_agent` + middleware).**
     - For: the most built-in pieces (summarization, user confirmation, PII,
       limits, retries).
     - Against: the heaviest option, with an API that has changed often; its
       checkpointer is a second conversation store; abstraction makes
       debugging harder.
  4. **Pydantic AI.**
     - For:
       - provider-agnostic models;
       - typed dependency injection (`deps` / `RunContext`), which fits
         D-009 exactly;
       - built-in user confirmation (`requires_approval` →
         `DeferredToolRequests` → resume with approve or deny);
       - history processors for compaction (to verify);
       - test models swapped in from the test suite, consistent with D-007;
       - lighter than LangChain, and Pydantic-native (pairs with FastAPI).
     - Against: less mature multi-agent orchestration (we have one agent);
       summarization isn't pre-built.
  5. **OpenAI Agents SDK.**
     - For: `needs_approval` user confirmation, sessions.
     - Against: built around OpenAI's Responses API; other providers are
       second-class via LiteLLM, which is in tension with D-033.
  6. **Not a fit:** LlamaIndex (RAG-centric; we aren't doing RAG);
     CrewAI/AutoGen (multi-agent); DSPy (prompt optimization); Vercel AI
     SDK/Mastra (TypeScript-only).
- **Recommendation:** Pydantic AI. It covers the abstraction, DI-scoped
  tools, user confirmation and testing with less weight than LangChain. We
  write compaction ourselves as a history processor, which is the
  context-engineering part we want to own and show anyway. Fallback:
  LangChain, if we'd rather have pre-built summarization.
- **Status:** Open (Q1).

---

## D-042 — Reopen caching and preference-memory designs
- **Question:** Are the caching design (D-039) and the preference-memory
  design (D-024/D-037) settled?
- **Considered:** keep them as Decided, or reopen them for further
  discussion.
- **Decision & rationale:** Reopen both. Sam wants to discuss caching on the
  filesystem further, and preference memory needs more design work before
  building. D-039, D-024 and D-037 stay in the log as **drafts** (including
  the `remember_preference` schema and test list). Tracked as Q5 and Q6 in
  `open-tasks.md`.
- **Status:** Decided (Sam).

---

## D-043 — Context budget & compaction design (layered defenses)
- **Question:** How do we keep each model request within budget, across
  long histories, tool-heavy turns, and turns that grow without tools,
  without silently dropping context?
- **Considered:**
  1. Compaction only, at a fixed message count (the original N = 20 idea).
     Fails on oversized single turns and on growth that doesn't come from tools.
  2. Truncating or eliding tool-result payloads. Rejected (Sam): it silently
     excludes valuable context.
  3. Capping tool output. Rejected as stated: "show me every X" would get a
     wrong answer silently.
  4. Layered defenses, applied most specific first (adopted). Normalized with
     an independent second-model review; research verified against Anthropic,
     OpenAI, Pydantic AI, MemGPT/Letta, Manus, Docker, Inspect, LangWatch.
- **Decision & rationale:** In priority order:
  1. **Request budget.** Budget the *whole* request: fixed prefix +
     per-user context + history + current input + a reserve for tool results
     and output. The history budget B is derived from it. Two kinds of limit:
     a *soft* budget (B: cost, latency, context rot; the one that actually
     bites) and *hard* limits (model window, output cap).
  2. **Size check before every model call**, including the calls after tool
     results within a turn.
  3. **Compaction.**
     - Trigger at **75%** of B (Sam). Trade-off: more summarization calls in
       exchange for headroom.
     - Compact down to ~40% of B.
     - Retention counted in **tokens**, with a floor of whole turns (Sam).
     - The compaction unit is a complete turn (Sam), tracked by our own
       `turn_id`.
     - Least-lossy order: first clear stale tool results *restorably*
       (keep the call/result pair plus a reference); then summarize whole turns
       into a **structured schema** (Sam: codified, not free-form).
       *Amended 2026-11-17 (Sam, D-091):* the format we validate is a fixed
       template with required headings, written by the Harness summarizer
       and checked before saving. A Pydantic schema replaces it only if app
       code ever needs to read individual fields.
     - Must-survive facts live in structured stores. A memory-pressure warning
       and pre-eviction extraction are designed, not built.
  4. **Tool and data layer first.**
     - Exact SQL filtering and aggregation for correctness ("how many / which
       ones").
     - Paginated list tools return `total_count` and `next_cursor`, and always
       state when results are partial.
     - An oversized single result is stored and read back by reference.
     - The app pages long lists through REST, bypassing the LLM.
  5. **Growth that doesn't come from tools.** A max user-message size;
     output-validation retries capped at 1, with a plain-text fallback; a max
     output token setting plus an output reserve.
  6. **Fail loudly** (error event + log) only if all of the above fail.
     Never silent loss.
  - **Required evals:** fact retention across compaction; the only qualifying
    product beyond page 1 is still found or counted correctly; oversized input
    is rejected cleanly; retry exhaustion falls back gracefully.
  - **Settles Q3:** execution is layered. Background compaction starts at the
    75% trigger; the pre-flight check compacts inline if needed.
- **Status:** Decided (Sam, 2026-11-16, "for now"). Where the MVP stops and
  design-only begins is to be settled at build time (open-tasks T14). Refines
  D-014, D-028, D-038. Flagged for the presentation as a hard problem
  (summary-notes.md).

---

## D-044 — Agent framework: Pydantic AI (settles Q1)
- **Question:** What implements the LLM abstraction (D-033), the tool loop,
  streaming, compaction hooks and auth-scoped tools?
- **Considered:** our own adapter; LiteLLM plus our own loop; LangChain v1;
  Pydantic AI; the OpenAI Agents SDK (full write-up in D-041). LlamaIndex,
  CrewAI/AutoGen, DSPy and Vercel AI SDK/Mastra were not a fit.
- **Decision & rationale:** **Pydantic AI** (implies Python). Dependencies are
  pinned through the normal backend lockfile. What we rely on:
  1. It supports multiple providers. The provider is chosen in configuration,
     and provider names stay out of Capper's application logic (D-033).
  2. Typed `deps` / `RunContext` for tools scoped to the authenticated user
     (D-009).
  3. `run_stream_events()` for streaming typed events (D-018).
  4. `CancellationToken` / `RunCancelled` and built-in continuation for Stop
     (D-046).
  5. `TestModel` / `FunctionModel` / `Agent.override` for tests (D-007).
  6. It assembles each request and applies provider caching through
     configuration (D-048).

  Acknowledged, decided later: approvals (`requires_approval`) are designed
  in T3. Whether we need the Harness add-on is decided in T14; if a Harness
  feature fits, we use it directly, with no wrappers.
- **Status:** Decided (Sam, 2026-11-16). Supersedes D-022 (LangChain); closes
  D-041.

## D-045 — Web framework and data layer: FastAPI + async SQLAlchemy (settles Q7)
- **Question:** FastAPI or Django (+ Django Ninja), and which database layer?
- **Considered:**
  1. Django + Ninja: ORM, migrations and admin built in, strong conventions;
     only a partly async ORM, and unused weight (sessions, templates).
  2. FastAPI: async throughout, built-in typed schemas and OpenAPI; ORM and
     migrations added separately.
  3. Database layer for FastAPI: SQLAlchemy 2.0 ORM + Alembic, SQLModel, or
     SQLAlchemy Core.
  4. SQLite tuning: WAL mode and lock timeouts.
- **Decision & rationale:**
  1. **FastAPI**, chosen on architecture (Sam's fluency is not a factor). No
     admin screens in the MVP.
  2. **SQLAlchemy 2.0 ORM + Alembic.** An ORM is wanted, and so is keeping
     database models separate from API schemas, which rules out SQLModel.
  3. **Async engine with `aiosqlite`.** The app is async, so a sync driver
     would pause the event loop on every query. Moving sync → async data
     access later is expensive; moving SQLite → a server database later is
     cheap.
  4. **WAL mode and lock-timeout tuning not adopted.** With short
     transactions, write concurrency is a non-issue at POC scale (code
     standard 6.3: transactions are never held open across a model call or a
     stream).
- **Status:** Decided (Sam, 2026-11-16). Presentation notes: the data layer
  was a greenfield choice (for a real client we'd weigh their existing driver
  and data layer), and SQLite's one-writer limit is a future concern.

## D-046 — Stop vs. disconnect; stopped turns are kept (settles Q8)
- **Question:** Do we expose a stop control, and what happens to a stopped
  turn?
- **Considered:** mockup R-12 shows the send button becoming a stop button,
  so it earns its place. For stopped turns: (A) exclude them from later
  context ("the user didn't want to share that"), which needs a custom filter
  on every context path plus a history integrity check; (B) keep what
  happened and continue with the framework's built-in handling.
- **Decision & rationale:**
  1. A dedicated `POST /v1/conversation/stop`, scoped to the user, with no
     ID.
  2. **Disconnect ≠ stop.** On disconnect, generation finishes in a
     background task and is saved; the app reloads history. Resumable live
     streams are a design target.
  3. One active turn per user, enforced server-side (409 on conflict).
  4. **Option B:** "Stop ends generation. Save what happened. The next
     message continues the conversation using Pydantic AI's built-in
     handling." On stop, the user's message, any partial reply and the
     framework's interrupted state are saved. No custom history filter, no
     integrity check, no UI marker. A closed stopped turn follows the normal
     compaction rules (D-043). Pending approvals on Stop belong to T3.
  5. **One regression test:** stop a reply, send "Actually, just snacks",
     and verify the new run still has the original request in context.
- **Status:** Decided (Sam, 2026-11-16). Refines D-018. Option A was the first
  choice and was reversed for simplicity and dialogue coherence
  (summary-notes.md).

## D-047 — LLM provider and models: OpenAI, two model settings (settles Q2)
- **Question:** Which provider and model(s) for the MVP, given the
  provider-agnostic design (D-033)?
- **Considered:** Anthropic vs. OpenAI (Sam has keys for both); originally
  argued on caching features (D-021), which stopped mattering once Pydantic AI
  handles caching through configuration (D-048). OpenAI models compared from
  first-party docs: `gpt-6-astra`, `gpt-6.1-sol`, `gpt-6.1-terra`,
  `gpt-6-luna`. The GPT-5 family shuts down on Dec 11, 2026, so it was
  excluded.
- **Decision & rationale:**
  1. **OpenAI for the MVP.** Provider and model are configuration.
  2. **Two model settings:** a chat model and a compaction model, so
     summaries and cleanup can use a cheaper model (a cost-design point for
     the presentation).
     - Chat: `gpt-6.1-terra` (fast, positioned for "clear, natural
       writing", half Sol's price). Fallback `gpt-6.1-sol` if the evals
       require it, as a configuration change.
     - Compaction: `gpt-6-luna` ("most efficient model for focused,
       high-volume tasks"; input about 1/10 of Terra's price).
  3. **Evals cover the MVP build only**; no cross-provider runs.
  4. **OpenAI specifics, all in configuration** (details on T4): the
     Responses API is selected by the model string, inside the adapter;
     `openai_reasoning_context` is set explicitly (`current_turn`) because
     Capper manages its own context; no OpenAI server-side conversation
     state or compaction; OpenAI does not keep its own copy of our responses
     (T10). Compaction is triggered by the application, never by a model tool
     call.
- **Status:** Decided (Sam, 2026-11-16). Supersedes D-021.

## D-048 — Provider caching mechanics belong to the framework (cleanup)
- **Question:** Do the earlier caching decisions still hold after choosing
  Pydantic AI and OpenAI?
- **Considered:** D-005, D-021, D-029 and D-039 were written before Q1, against
  Anthropic's API: its render order (tools → system → messages), its "cache
  breakpoint" markers and its `cache_control` field.
- **Decision & rationale:** Those provider-specific mechanics are superseded.
  Pydantic AI assembles each request and applies provider caching through one
  `cache` setting. Our job is content stability: the most stable content
  first, nothing volatile in the tool definitions or fixed instructions,
  per-user context and the conversation after (code standard 4.2, rewritten
  in neutral terms). The principle of D-005 (stable first) stands.
- **Status:** Decided (Sam, 2026-11-16). Supersedes the breakpoint mechanics
  in D-005, D-021, D-029 and D-039.

## D-049 — MVP content set, taxonomy and do-no-harm policies (settles Q4)
- **Question:** What does Capper know, and how does each kind of content
  reach the model? (Settles D-031 and P-012.)
- **Considered:** D-031's four classes; long documents vs. "irrelevant
  context always hurts" (removed from the MVP by interviewer answer 4); an
  always-on allergy rule vs. on-demand policies. Research: progressive
  disclosure (Anthropic Agent Skills); its weakness, that the model must
  choose to load a policy (Vercel's agent evals); prompt rules as one layer
  among several (Microsoft); standard hazard categories (MLCommons
  AILuminate).
- **Decision & rationale:** D-031's four classes, applied to the MVP:
  1. **Operator policy**, authored by us (assumptions and boilerplate are
     fine), in three sibling subclasses: scope charter; persona and voice
     (always loaded); **do-no-harm policies** (loaded on demand).
     - Every turn: a short core drawn from standard categories (no
       specialized medical, legal or financial advice; no guessing on health
       or safety facts; crisis → resources and hand-off) plus a trigger line:
       call `read_policy(topic)` before answering anything touching health,
       safety, allergies, diet or medical conditions, children's safety, or
       distress.
     - `read_policy(topic)` returns one detailed policy (allergens and food
       safety, dietary and medical claims, child safety, product misuse,
       crisis).
     - Evals per policy area measure trigger recall (must fire / must not
       fire).
  2. **User-facing knowledge:** Referral FAQ, Program Rules and the
     product-knowledge doc (D-035), sent in full every turn.
  3. **Live data:** tools only.
  4. **Internal-only:** excluded by default, because the ingestion manifest
     is an allowlist.

  Also: conflicts and placeholder values in the source documents are
  ingestion concerns (the canonical reference resolves conflicts, with the
  Program Rules over the FAQ as a flagged assumption, and marks example
  values as examples), not solved for the MVP. Questions the content can't
  answer are handed off to support, with one eval case.
- **Status:** Decided (Sam, 2026-11-16). Decides D-031. Presentation
  footnotes (summary-notes.md): the "if desired" safety net (a cheap check
  agent in parallel), internal-only content, long documents.

## D-050 — Content stored in a database table; caching (settles Q5)
- **Question:** Where does ingested content live, what is cached, and how do
  changes take effect?
- **Considered:** D-039's draft (a bundle on disk, an in-process rendered
  prefix, the provider cache); a database table; app-side caches; per-user
  vs. shared `prompt_cache_key`; pre-warming.
- **Decision & rationale:**
  1. **Content lives in a simple database table**, one row per canonical
     document. A filesystem bundle would need a deploy for every FAQ update,
     which is not production-ready. Per-entry rows are noted as a
     possibility for an admin portal.
  2. **Ingestion inserts rows and never edits them**; new rows are marked
     active. The content version is a hash over the active rows.
  3. **The service reads the active documents once at the start of each
     turn**, so a turn is consistent and content changes need no deploy or
     restart. The same rows render the same bytes, so the provider cache
     keeps hitting. Do-no-harm policies are rows in the same table.
  4. **Versions attach to conversation history:** each assistant message and
     compaction summary records the content version and model it used.
  5. **No app-side caches** of documents, data or LLM answers (code standard
     4.8). Provider caching is on through Pydantic AI (implicit, 30-minute
     default), with a **per-user opaque `prompt_cache_key`** (prevents
     cross-user cache probing). **No pre-warming.**
  6. **MVP ingestion just needs to work**, with barebones evals. The S3
     trigger, inactive rows, an eval gate before activation and an in-memory
     copy are design only.

  The ingestion/service boundary (D-032) is unchanged; the shared contract
  module now defines the table and its read/write functions.
- **Status:** Decided (Sam, 2026-11-16). Supersedes D-039 and the filesystem
  bundle in D-016's MVP section.

## D-051 — Preference memory: avoid list + guidance notes (settles Q6)
- **Question:** How does Capper remember a user's lasting preferences, and how
  are they enforced?
- **Considered:** D-024's typed tool with kinds; a separate store vs. history
  and summaries only; per-field structure. Research on standard approaches:
  the CoALA memory taxonomy (semantic, procedural, episodic) as used by
  LangGraph; profile vs. collection storage; mem0's add/update/delete
  operations; Letta's memory blocks; ChatGPT's saved memories; the FDA's nine
  major allergens as a controlled list.
- **Decision & rationale:** two things for the MVP, stored outside the
  conversation so compaction can't lose them:
  1. **A product avoid list**, enforced by the catalog query.
  2. **Short, editable guidance notes** for everything else (e.g. "don't
     greet me with good morning after 11", "my kid no longer goes to
     Lincoln"). The linked school stays an account setting.

  Behavior:
  1. Save clear requests and tell the user what was saved (code standard 3.3
     exception). Add, update or remove one item at a time.
  2. Guidance personalizes Capper's responses within its scope and safety
     rules.
  3. Capper can remember an allergy without promising its recommendations are
     safe.
  4. On removal, Capper says "I removed that from your saved guidance." The
     original chat and any existing summary may still contain it.

  Skipped for now: the memory taxonomy, an allergen enum, dietary categories,
  background extraction and broader context redaction. Advanced filtering
  (e.g. allergen tags on products) is a design/presentation nod.

  D-037's required tests, adapted to this design: validation (unknown
  product, note length); scoping (no `user_id` parameter; cross-account
  tests); the catalog query excludes avoided products; add, update and remove
  of a single item; phrasing evals.
- **Status:** Decided (Sam, 2026-11-16). Supersedes D-024 and D-037.

---

## D-052 — Documentation clarifications (grooming pass)
- **Question:** Which statements in earlier entries need a label or say more
  than the design delivers, given that entries are never rewritten?
- **Considered:** rewriting the entries (rejected: the log is append-only) vs.
  one clarification entry linked from the index.
- **Decision & rationale:**
  1. **D-001:** that manually refactoring AI-assisted code satisfies the
     brief's rule ("submitting code produced by generative AI is prohibited")
     is Sam's interpretation, **not confirmed with the interviewer**. If the
     submission includes manually refactored AI-generated code, ask the
     interviewer before relying on it (open-tasks.md).
  2. **D-003:** the conversation log is our chosen supporting material, not a
     requirement of the brief.
  3. **D-047:** "OpenAI does not keep its own copy of our responses" is too
     strong. Precisely: Capper owns conversation state; requests set
     `store: false`, which opts out of OpenAI storing response state for
     reuse; OpenAI's separate retention policy (e.g. abuse monitoring) still
     applies and is documented in the privacy write-up (T10).
  4. **D-050:** a per-user `prompt_cache_key` separates provider cache reuse
     by user. OpenAI says separate keys help prevent cross-user cache probing;
     the key alone doesn't "prevent" it.
- **Status:** Decided (Sam, 2026-11-16, from the documentation review).
  Clarifies D-001, D-003, D-047, D-050.

## D-053 — Conflicting referral sources in the demo: hand-curated, Rules win
- **Question:** The FAQ and Program Rules disagree (the bonus trigger, late
  attribution), and D-049 sends both in full every turn. What does Capper see
  in the demo?
- **Considered:**
  1. Send both and let the model choose: Capper sees two answers, and the
     mockup's referral flow (R-22) follows the Rules.
  2. Automated conflict resolution at ingestion: design-only per D-049.
  3. Curate the referral text by hand for the demo.
- **Decision & rationale:** Option 3. Where the FAQ and Program Rules
  conflict, the curated text uses the Rules' version, as an **explicit demo
  assumption to confirm with the client** (it matches R-22). Automated
  conflict resolution stays design-only.
- **Status:** Decided (Sam, 2026-11-16, from the documentation review).
  Refines D-049.

---

## D-054 — MVP action tools: no records created; confirmation designed, not built
- **Question:** Which action tools does the MVP include, and is the
  user-confirmation flow (D-011, D-026) built?
- **Considered:** a support-ticket hand-off and a stored grocery list (both
  would need confirmation) vs. what the product spec actually shows.
- **Decision & rationale:** The MVP goal is everything in the product spec,
  and nothing more.
  1. **Hand-off to support (R-03)** tells the user how to reach support. It
     creates no ticket; a ticket was never in the spec.
  2. **Grocery list (R-08):** Capper offers it as in the mockup; if the user
     accepts, the list is shown in the reply as a response part. No record is
     created.
  3. **Confirmation flow:** designed (T3), not built for the MVP, since no MVP
     tool creates, changes, sends or deletes anything outside the user's own
     memory (code standard 3.3 exception).
- **Status:** Decided (Sam, 2026-11-16). Refines D-011 and D-026 for the MVP.

## D-055 — Example values are handled at ingestion, including the demo
- **Question:** How are the Rules' example values ("e.g. $5", "e.g. 48
  hours") kept from being stated as fact?
- **Considered:** already settled: ingestion produces the canonical reference
  (D-049), and the demo's referral text is curated by hand (D-053).
- **Decision & rationale:** Ingestion handles it. The canonical text marks
  example values as examples; for the demo, that happens in the same
  hand-curation pass as the conflicts (D-053). No prompt rule and no separate
  mechanism. Recorded so it isn't raised again.
- **Status:** Decided (Sam, 2026-11-16). Refines D-049 and D-053.

---

## D-056 — Rich response parts: streamed text plus typed cards from verified data (W1)
- **Question:** How does Capper produce the mockups' rich replies (several
  bubbles, lists, steps with headings, product and promotion cards), and how
  are they validated and streamed?
- **Considered:**
  1. Markdown text only: simplest, but no structured IDs, so cards can't be
     built or checked.
  2. Fully structured output: everything typed, but streaming relies on
     Pydantic's experimental partial validation, and the model writes card
     contents itself.
  3. Hybrid ("generative UI" via tool calls, as in Vercel's AI SDK and
     assistant-ui's Tool UI).
- **Decision & rationale:** Option 3.
  1. **Text streams as NDJSON events.** Basic Markdown is fine for lists,
     steps and headings.
  2. **Product and promotion cards are typed events built from validated
     database records.** The model supplies only IDs through display tools;
     the server checks them, builds the card from the database, and emits the
     event in stream order. Unknown or avoided IDs never become cards.
  3. **The contract supports the mockup behaviors; the mobile app decides how
     to render them.** We're defining the API for a hypothetical existing app.
     The demo web client stays thin.
  4. **The card payload is saved as it was sent**, so reloading the
     conversation shows what the user originally saw.
  5. **Product claims in free text:** a prompt rule and an eval are enough for
     the MVP; the cards themselves come from verified data.
- **Status:** Decided (Sam, 2026-11-16). Refines D-018; applies code standard
  4.7.

---

## D-057 — Architectural boundary: generic capabilities, not use-case features
- **Question:** Food examples from the spec (allergies, diets, grocery lists)
  kept turning into proposed features, schemas and categories. Where is the
  line?
- **Considered:** designing from the mockup flows down to features (what
  happened, and the source of the drift) vs. designing from capabilities down,
  with the mockups as examples.
- **Decision & rationale:** Capper is built from generic capabilities:
  1. **Tools look up and modify data.**
  2. **The agent builds responses** for the user.
  3. **The agent saves relevant data** about the user (generic guidance notes;
     the avoid list, D-051).

  No code, tool, schema or category is specific to a use case or domain.
  Domain specifics (food, allergies, diets, grocery lists) appear only in
  **content** (e.g. a do-no-harm policy document in the content table) and as
  **example cases in tests and evals** (e.g. an allergy as the example that
  tests "health-related guidance never produces a safety guarantee"). They
  never shape tools, schemas or code paths. Check before proposing anything:
  is it a generic capability, and would it still make sense if the catalog
  were hardware instead of groceries?

  Reframed entries (append-only, so clarified here and in the index):
  1. **Mockup requirements table (R-01..R-22):** behaviors to support through
     generic capabilities; the food details are examples.
  2. **D-008:** no domain-specific product attributes (allergen or dietary
     tags); products get only the generic fields the tools need.
  3. **D-049:** the policy topics are content, loaded on demand; nothing about
     them is coded.
  4. **D-051:** guidance notes are generic. A note may hold a sensitive detail
     (e.g. an allergy), and Capper never turns it into a safety guarantee. An
     allergen enum and dietary categories aren't "skipped for now"; they're
     excluded by design.
  5. **D-054:** there is no grocery-list feature. Lists are ordinary composed
     responses.
- **Status:** Decided (Sam, 2026-11-16). Code standard 7.3.

---

## D-058 — MVP tool set (W2)
- **Question:** Which tools does Capper get for the MVP, and what does each
  take and return?
- **Considered:** a general query tool (rejected, code standard 3.2); the
  catalog in the prompt (doesn't scale; moves per-user filtering out of code);
  narrow tools grouped by D-057's capabilities.
- **Decision & rationale:** Narrow tools, each defined by the data it returns.
  A specific query returns a result set; a lookup scoped to the record type
  returns individual records. Lookups stay explicit (no generic card tool).
  Every tool takes `user_id` from auth only, has a strict schema, is
  audit-logged, and returns errors as results.
  1. **Result-set queries:** `search_products` (optional text query →
     products, avoided products excluded in code; paging fields per D-043,
     built per T14), `get_promotions` (active promotions, avoided products
     excluded).
  2. **User's own record:** `get_my_referral_code` (the code, or a clear "no
     code" result).
  3. **Content lookup:** `read_document` (a name from the fixed list of
     on-demand content documents → its text; replaces `read_policy`).
  4. **Record-type lookups that build cards (D-056):** `show_products`
     (product IDs) and `show_promotions` (promotion IDs). The server validates
     the IDs and emits typed card events from the database.
  5. **Saving user data (D-051):** `avoid_product` / `unavoid_product`;
     `add_guidance` / `update_guidance` / `remove_guidance`.

  From context, not tools: the user's name and linked school, guidance notes,
  the avoid list. Hand-off needs no tool (support details are content).
  **No product categories:** they aren't in the spec; they came from D-008's
  seed proposal. Purchase history is W3.
- **Status:** Decided (Sam, 2026-11-16).

---

## D-059 — Purchase history through a lookup tool (W3)
- **Question:** Does Capper use the user's purchase history, and how does it
  get it?
- **Considered:** not using it; a purchase summary in the per-user context on
  every turn; a result-set query tool.
- **Decision & rationale:** Recommendations are built on user context.
  Putting purchase history into every request is bloat, so it's exposed as a
  tool: `get_my_purchases` returns the user's recent purchases (product ID,
  name, quantity, date), limited, with paging per D-043. Scoped to the
  authenticated user (D-009). Persona content tells Capper to check it before
  recommending; an eval case checks that it does. An empty result (new user)
  means Capper asks instead (R-04).
- **Status:** Decided (Sam, 2026-11-16). Extends D-058.

---

## D-060 — Greeting, sessions and time (W4)
- **Question:** How does the greeting appear, what counts as a session, and
  how is time handled?
- **Considered:** a model-written greeting (an LLM call before the user
  speaks); an app-hard-coded greeting (bypasses the content pipeline); a
  content greeting stored in the transcript (forces a server-side session
  rule); server sessions from an inactivity gap; sessions from the auth
  session (Sam's suggestion).
- **Decision & rationale:**
  1. **Greeting (a sensible default, not an architecture question):** the
     greeting text is content (persona/voice document). The API delivers it,
     the app shows it when the chat opens, and it isn't stored in the
     transcript. No LLM call.
  2. **No server-side sessions in the MVP.** Nothing needs them: the app
     renders the date header from message timestamps, and session metrics
     can be derived from timestamps later. If sessions are ever needed, they
     come from the auth session, read statelessly from standard token claims
     (`auth_time` or `sid`) rather than an inactivity heuristic. Caveat:
     mobile logins can last weeks, so auth sessions are coarse.
  3. **Time:** timestamps are universal (UTC). The UX shows clock time in the
     user's time zone. The existing data has no user time zone, so the
     service uses a configurable default for anything time-aware; capturing
     the user's time zone is a presentation note (possible migration).
- **Status:** Decided (Sam, 2026-11-16). Supersedes D-036's "session
  boundaries are recorded".

---

## D-061 — LLM provider failures: one generic error; provider failover as the follow-up (W5)
- **Question:** What happens when the LLM provider fails (timeout, rate limit,
  server error, or an error mid-stream)?
- **Considered:** letting errors propagate; retrying only before the first
  token, then ending cleanly; adding a fallback model (Pydantic AI
  `FallbackModel`); failing over to another provider.
- **Decision & rationale:**
  1. **Retry only before the first token.** The OpenAI SDK's built-in retries
     (429 and 5xx, with backoff) handle transient errors before anything has
     streamed, with chat-sized timeouts instead of the SDK's 10-minute
     default.
  2. **Any error reaches the user as one generic error event**, including
     mid-stream, so the user is never left waiting. One generic error for
     every API error in the MVP: the simplest build, and user-retryable. What
     happened is saved like a Stop (D-046), and the next message continues
     normally. The error never names the provider (D-033).
  3. **Follow-up, designed for now:** failover to **another provider**, not
     just another model, so a rate limit or a full outage at one provider is
     no longer existential. Provider-agnostic design (D-033, D-044) makes it
     configuration (Pydantic AI's `FallbackModel` chains models across
     providers). Design points: fail over only before the first token; the
     fallback provider needs its own evals and settings (reasoning context,
     caching), and its data terms belong in the privacy write-up; the
     conversation history is stored in Pydantic AI's provider-neutral format,
     so a switch mid-conversation works. Noted for the presentation.
- **Status:** Decided (Sam, 2026-11-17).

---

## D-062 — Specs vs. evals: specs for deterministic parts, two evals to show the practice (W6)
- **Question:** What gets tested, what gets evaluated, and how do they run?
- **Considered:** real-model evals inside pytest behind a marker; two separate
  suites; an external eval platform.
- **Decision & rationale:** Unit and integration tests are **not** evals.
  Evals are tests against the probabilistic system. Build just enough evals to
  show we know how.
  1. **Specs (pytest) for the deterministic parts and context building**:
     auth and user scoping, tools (validation, the avoid-list filter, card
     building from records), content reads, context assembly, compaction
     selection, Stop and error persistence. Pydantic AI's `TestModel` /
     `FunctionModel` are injected from the test suite, and
     `ALLOW_MODEL_REQUESTS = False` blocks real model calls (code standard
     1.1). The D-046 stop/continue regression is a spec.
  2. **One tool-call eval** against the real model, for a single tool, to show
     the concept.
  3. **One answer-quality eval with an LLM judge**, implemented and left
     commented out, to show the ability to add it.
  4. Evals use Pydantic Evals under `evals/`, run only by an explicit command
     (never in CI by default), against a seeded database copy. Other eval
     cases named in earlier decisions (D-049, D-051, D-056, D-059) are
     documented as eval cases, not built.
- **Status:** Decided (Sam, 2026-11-17). Decides D-025 for the MVP. Open: how
  this squares with D-043's required evals (see open-tasks W6).

---

## D-063 — API contract (W7, T6)
- **Question:** What is the contract between the mobile app and Capper?
- **Considered:** the draft assembled from D-018, D-020, D-036, D-043,
  D-046, D-056, D-060 and D-061, plus four new choices (duplicate sends,
  reconnecting, bubble boundaries, greeting shape).
- **Decision & rationale:** Sensible defaults that match the underlying
  system and follow best practice (Sam). FastAPI generates the OpenAPI
  document.
  1. **Endpoints:** `GET /v1/conversation` (greeting and
     `turn_in_progress`); `GET /v1/conversation/messages?before=&limit=`
     (history, newest first, `{messages, next_cursor}`);
     `POST /v1/conversation/messages` (NDJSON stream; 409 if a turn is
     running; 422 if the text is empty or too long);
     `POST /v1/conversation/stop` (202, idempotent; "nothing to stop" is not
     an error).
  2. **Stream events:** `turn.start`, `text.delta` (Markdown), `card`
     (product or promotion, built from records), `turn.end` (`complete` or
     `stopped`), `error` (one generic code, then the stream ends).
  3. **Stored message:** `id`, `role`, `created_at` (UTC), `status`
     (`complete`, `stopped`, `error`), `parts` (text and card parts as sent).
  4. **Non-stream errors:** `{"error": {"code", "message"}}` for 401, 409 and
     422.
  5. **Duplicate sends:** an `Idempotency-Key` header; a retry with the same
     key returns the existing turn.
  6. **Reconnecting:** the app checks `turn_in_progress` and reloads history;
     resumable streams stay a design target (D-046).
  7. **Bubbles:** the app splits text at paragraph breaks and around cards;
     no extra event. **Greeting:** a list of text bubbles from content.
- **Status:** Decided (Sam, 2026-11-17). Assembles D-018, D-020, D-036,
  D-046, D-056, D-060, D-061. List paging through REST depends on T14.

---

## D-064 — What the MVP builds from D-043 (W8, T14)
- **Question:** Which layers of the context-budget design (D-043) does the MVP
  build, and do we use Pydantic AI's Harness add-on?
- **Considered:** building all of D-043; building the core loop with the rest
  as design; no compaction (rejected: it's the focus area).
- **Decision & rationale:**
  1. **Budgeting code is built**, so runaway requests can be identified while
     debugging. Limits are generous, with sensible defaults in configuration,
     tweaked as needed.
  2. **Every step of the trace is logged** with what's needed to debug it
     (code standard 8.6).
  3. **Compaction is built, including the background job** (production
     systems handle async work, and it isn't a large lift), with the size
     check before each model call compacting inline when needed (D-043's
     layered execution).
  4. **The Pydantic AI Harness is used** for clearing stale tool results and
     for oversized tool output, instead of building those ourselves. Its
     trade-offs are written up for Sam's later review (summary-notes.md, "For
     review later").
  5. **Also built:** `limit` and `total_count` on list tools (partial results
     are always stated), the message-size cap, one output-validation retry,
     a maximum output length, and the generic error (D-061).
  6. **Design-only:** cursor paging, the app paging long lists through REST,
     and the memory-pressure warning.
  7. **Demo:** the history budget is a real configuration value, so the demo
     can run with a small budget to show compaction in a short conversation
     (a setting, not a test switch).
- **Status:** Decided (Sam, 2026-11-17). Settles T14; refines D-043.

---

## D-065 — Which tool results stay verbatim (W9)
- **Question:** After a turn ends, how much of its tool activity does the
  model still see verbatim in later turns?
- **Considered:** everything verbatim until compaction; every call kept plus
  the last N results (older ones cleared by the Harness); only final text from
  earlier turns (breaks references like "the second one").
- **Decision & rationale:** Option 2.
  1. **All results from the current turn are kept until it finishes.**
  2. **The rolling limit applies only to tool results from completed turns:**
     the last 5 are kept verbatim (a configurable starting point); older
     ones are cleared, with their calls (tool name and arguments) still
     visible so the model can re-run a tool.
  3. **The retention count and the per-turn tool-call limit are tuned
     independently.**
  4. Whole turns, tool exchanges included, are summarized at compaction, and
     the structured summary keeps the IDs mentioned (D-043).
- **Status:** Decided (Sam, 2026-11-17). Refines D-043 and D-064.

---

## D-066 — Privacy system is design-only; user-shared content is handled generically (W10)
- **Question:** How does Capper handle personal information about other
  people (R-21, "Sally")?
- **Considered:** treating it as a separate concern with its own rules
  (detection, redaction, content rules) vs. treating it as one example of
  what users share.
- **Decision & rationale:** It isn't its own concern. Users say all kinds of
  things about people, events, thoughts and more; information about other
  people is an illustrative example, not the system. The privacy system is
  **design only, for discussion, not MVP**, written up in summary-notes.md:
  purging conversation history and targeted redaction ("don't bring that up
  again": redact messages and history, then recompact), each with its design
  difficulty and trade-offs. The MVP keeps what's already decided: removal
  from saved guidance with honest wording (D-051), redacted logs (code
  standard 5.2), no provider response state (D-052).
- **Status:** Decided (Sam, 2026-11-17). Feeds T10.

---

## D-067 — Conflicting guidance notes: newer notes supersede earlier ones (W11)
- **Question:** What happens when a saved guidance note conflicts with another
  note, or with something the user says later?
- **Considered:** the model resolving conflicts with its tools (update or
  remove, ask when unsure); conflict detection in code (not possible
  generically for free text, D-057); keeping everything with the newest
  winning.
- **Decision & rationale:** For the MVP, the model is directed to treat newer
  notes as superseding earlier ones. Notes are shown in order, with their
  dates, so the model can tell which is newer. A more robust version is
  design work, noted in summary-notes.md.
- **Status:** Decided (Sam, 2026-11-17).

---

## D-068 — Limits on saved guidance (W12)
- **Question:** How do we keep saved guidance from growing without bound?
- **Considered:** (researched) production memory systems combine a hard
  capacity limit (ChatGPT saved memories, Letta block limits), background
  consolidation (Letta sleep-time agents, mem0's consolidation, Claude Code's
  Auto Dream), expiry (mem0's `expiration_date`, Zep's validity intervals),
  and decay for retrieval-based systems (not applicable: all notes are in
  context). Options: caps only; caps plus normalized notes plus optional
  expiry; that plus background consolidation.
- **Decision & rationale:** Option 2, with sensible MVP defaults
  (configurable):
  1. **Caps:** at most 30 guidance notes of up to 300 characters each
     (roughly 2 to 3 thousand tokens when full); the avoid list is capped at
     100 products. When a cap is hit, the tool returns a clear result and
     Capper offers to remove or merge notes (`update_guidance` plus
     `remove_guidance`).
  2. **Normalized at save time:** the tool description has the model write
     each note as a short statement in a consistent form.
  3. **Optional expiry:** a note can carry an `expires_at`; notes are
     permanent by default; expired notes are hidden from the model, not
     deleted.
  4. **Background consolidation** (merging duplicates and conflicts,
     pruning stale notes) is not in the MVP; it's in summary-notes.md for a
     closer look before the presentation.
- **Status:** Decided (Sam, 2026-11-17). Refines D-051 and D-067.

---

## D-069 — Language: English only for the MVP (W13)
- **Question:** What does Capper do when a user writes in a language other than
  English?
- **Considered:** English only; replying in the user's language with English
  content; full localization.
- **Decision & rationale:** The MVP is English only. The persona content tells
  Capper to reply in English. How systems like this expand into other
  languages is a topic Sam wants to understand for the presentation
  (summary-notes.md, "For review later").
- **Status:** Decided (Sam, 2026-11-17).

---

## D-070 — Users with little data: best effort, with a popular-products fallback (W14)
- **Question:** What does Capper do for a user with little to personalize
  from (no purchases, no linked school, no saved guidance)?
- **Considered:** content only (ask instead of guessing); a special "new user"
  mode in code (use-case code, D-057).
- **Decision & rationale:**
  1. **Best effort with what we know.** One purchase, the user's location, or
     anything else is enough for a naive recommendation.
  2. **Voice:** a simple acknowledgement in the persona content that Capper
     learns the user's habits as they use the platform, or an invitation to
     say what they're interested in. Designing interest collection is out of
     scope.
  3. **Fallback when there's no relevant data: popular products near the
     user.** A simple query exposed as a result-set tool,
     `get_popular_products`: products ranked by purchases among users linked
     to the same school (the only location data we have), falling back to all
     users if no school is linked. The result says which basis it used, so the
     message adjusts programmatically ("popular with families at your school"
     vs. "popular overall").
  4. **Out of scope, noted in summary-notes.md to think through:** feedback on
     recommendations to learn preferences (part of the user feedback design,
     T8); collaborative filtering ("people who bought what you bought also
     bought...").
- **Status:** Decided (Sam, 2026-11-17). Extends D-058 and D-059.

---

## D-071 — Data model (T16)
- **Question:** What schema does the MVP need?
- **Considered:** the needs set by earlier decisions; one message table
  (Pydantic AI's format only) vs. two (our transcript plus the framework's
  history).
- **Decision & rationale:** Sensible details that achieve the stated goals
  (Sam). The provided tables stay as the existing app's schema, plus a
  nullable `Products.image_url` for cards. New tables (snake_case):
  1. `turns`: status, idempotency key (unique per user), model, content
     version; a partial unique index enforces one active turn per user.
  2. `messages`: the user's transcript in our own stable format (text and
     card parts as sent), append-only.
  3. `model_messages`: Pydantic AI's serialized history (tool calls, results,
     interrupted state), append-only; clearing and compaction change only the
     view built from it. Two tables so a framework upgrade can't break old
     transcripts.
  4. `summaries`: structured compaction summaries with a watermark
     (`covers_through_turn_id`), model and content version.
  5. `guidance_notes` (text up to 300 characters, optional `expires_at`) and
     `avoided_products`.
  6. `content_documents`: insert-only, one active row per name, `load` is
     `always` or `on_demand`; the content version is a hash over active rows.
  7. `promotions` (generic title and description, dates) and
     `referral_codes`.
  8. `tool_calls`: the audit log, arguments redacted.

  No job queue table (in-process background job with the inline fallback), no
  "participating" flag, no categories. Seeds cover the mockup products with
  images, active promotions, referral codes (one user without), purchases
  across several users per school, a user with guidance and avoided products,
  a cross-account pair, the control user, and a brand-new user.
- **Status:** Decided (Sam, 2026-11-17). Settles T16; built in B3.

---

## D-072 — System design: structure and request flow (T1)
- **Question:** How is the service structured, and how does a turn flow
  through it, so the code is clean, modular, extensible and readable?
- **Considered:** best practice for FastAPI + async SQLAlchemy + Pydantic AI:
  organizing by domain (the zhanymkanov FastAPI guide); layers with
  dependencies pointing inward (Cosmic Python); Pydantic AI's dependencies
  dataclass; a session per unit of work; strict typing. Missing standards
  were added (code standards 6.4–6.6, 7.4–7.7, 8.6–8.8).
- **Decision & rationale:**
  1. **Structure:** domain packages under `src/capper/` (auth, accounts,
     catalog, memory, conversation, context, agent), each with the same shape
     (`models.py`, `repository.py`, `service.py`, plus `api.py` and
     `schemas.py` where it has routes); `app.py` as the single composition
     root; `content_bundle` and `ingestion` as separate modules; `scripts/`,
     `tests/` (mirroring `src/`), `evals/`, `alembic/`.
  2. **Request flow** for sending a message: the route authenticates,
     validates and calls the service; the service starts the turn in a short
     transaction (one active turn per user, idempotency); generation runs in
     a lifespan-owned background task feeding a queue the route streams from
     (a disconnect doesn't cancel); the context is assembled by a pure
     function from small loaders; the agent runs with `run_stream_events`,
     with a history processor doing the size check, Harness clearing and
     inline compaction; tools are thin adapters over services that write
     their audit row; events map to NDJSON; the end of the turn (or a stop or
     error) is persisted in one short transaction; compaction runs afterwards
     in the background when the history passes 75% of the budget.
  3. **Tooling defaults:** pyright in strict mode alongside ruff; Alembic
     migrations in `alembic/`.

  A starting point; Sam reviews and refactors after the MVP.
- **Status:** Decided (Sam, 2026-11-17). Settles T1.

---

## D-073 — Confirmation flow, design only (T3)
- **Question:** How would an action that needs the user's approval work?
- **Considered:** the rules in D-011 and D-026, code standards 3.3 and 3.4,
  and Pydantic AI's built-in approval support (`requires_approval`).
- **Decision & rationale:** Design only; the MVP has no such action (D-054).
  Sensible defaults (Sam):
  1. A tool marked `requires_approval` pauses the run instead of executing.
  2. The server stores a pending action (user, turn, tool, validated
     arguments, created and expiry times, status: `pending`, `approved`,
     `declined`, `expired`, `cancelled`); only the stored arguments ever run.
  3. A `pending_action` stream event tells the app; the turn ends waiting.
  4. `POST /v1/conversation/pending-actions/{id}/approve` or `/decline`,
     scoped to the user (another user's ID is a 404). Approving resumes the
     run with the stored arguments; the tool still enforces its own
     authorization (code standard 3.4).
  5. Declining returns "declined by the user" to the model as the tool
     result.
  6. Single use; expires after 15 minutes (configurable) and then counts as
     declined.
  7. The proposal and the decision are both audit-logged.
  8. **Stop** while an action is pending cancels it, and **a new message**
     instead of a decision does the same; the model sees "declined", so every
     tool call keeps a result.
  9. Data model when built: a `pending_actions` table (not in D-071).
- **Status:** Decided (Sam, 2026-11-17). Settles T3 and the pending-approval
  part of Q8.

---

## D-074 — History search: built with SQLite full-text search (T5)
- **Question:** Does the MVP expose full history lookup? Sam's acceptance of
  compacting down to ~40% of the budget rested on it ("should be fine since we
  expose full history lookup").
- **Considered:** design only; keyword search with SQLite's built-in FTS5; a
  semantic search with embeddings (a new dependency, more than the MVP needs).
- **Decision & rationale:** Build it, with best practice and sensible
  defaults (Sam):
  1. **Tool:** `search_my_history(query)`, a result-set query (D-058)
     returning up to 5 matches, ranked by relevance (FTS5's `bm25`), each with
     its date and a short snippet (FTS5's `snippet`).
  2. **Index:** an FTS5 table over the text of user and assistant messages,
     with the user ID and message ID stored alongside (not searchable); the
     `porter unicode61` tokenizer (English only, D-069). The app writes the
     index row in the same transaction as the message, so they never drift.
     Created by an Alembic migration.
  3. **Scoped by user inside the query** (`MATCH` plus `user_id = :user`),
     never filtered afterwards (code standard 2.2).
  4. **Query text is quoted term by term** before it reaches `MATCH`, so the
     model's or user's input can't inject FTS5 syntax.
  5. **Results go to the model as data, never instructions** (code standard
     4.6). Card payloads and tool data aren't indexed.
  6. **Privacy design** (summary-notes.md): a purge or redaction must also
     remove the matching index rows.
  7. Specs cover scoping, matching and query quoting; an eval case is
     written up (D-062).
- **Status:** Decided (Sam, 2026-11-17). Settles T5; extends D-058 and D-071;
  keeps D-043's premise for the 40% target true.

---

## D-075 — Observability (T7)
- **Question:** How do we see what the service is doing: logs, traces, token
  usage, cost and cache behavior?
- **Considered:** logs only; adding OpenTelemetry tracing (built into
  Pydantic AI); a hosted observability product.
- **Decision & rationale:** Sensible defaults and best practice (Sam):
  1. **Built:** step-by-step logs tied by turn ID (D-064, code standard 8.6),
     plus **one summary log line per turn**: input, output and cached tokens;
     estimated cost (tokens times the configured price per model); time to
     first token and total time; tool-call count; whether compaction ran; the
     final status. Cache hit rate = cached tokens / input tokens, from
     OpenAI's usage fields.
  2. **Design only:** OpenTelemetry tracing via Pydantic AI's built-in
     instrumentation (agent runs, model calls, tool calls as spans) plus
     FastAPI request spans, exported to the client's backend. Message content
     capture must be off (`include_content=False`); Pydantic AI captures it by
     default, which would break code standard 5.2.
  3. **Design only:** dashboard metrics: tokens and cost per turn, cache hit
     rate, time to first token, error and stop rates, compactions per
     conversation.
- **Status:** Decided (Sam, 2026-11-17). Settles T7.

---

## D-076 — User feedback, built in the MVP (T8)
- **Question:** How do users tell us an answer was good or bad, and how does
  that feed improvement?
- **Considered:** design only (no feedback control in the mockups) vs.
  building it.
- **Decision & rationale:** Part of the MVP (Sam).
  1. **Captured:** a thumbs up or down on an assistant message, with an
     optional short comment. Later, the same mechanism covers feedback on
     recommendation cards (D-070).
  2. **API:** `POST /v1/conversation/messages/{id}/feedback`, scoped to the
     user (another user's message is a 404); one rating per message, a later
     rating replaces the earlier one. Extends D-063.
  3. **Data:** a `message_feedback` table (user, message, rating, comment,
     created time), linked through the turn to the model, content version and
     logs behind the answer. Extends D-071.
  4. **Use:** error analysis (D-025): read poorly rated turns, group the
     failures, turn recurring ones into eval cases.
  5. Comments are user text: data, never instructions (code standard 4.6),
     never logged verbatim (5.2).
- **Status:** Decided (Sam, 2026-11-17). Settles T8.

---

## D-077 — Security audit of the design (T13)
- **Question:** Does the design hold up against the known risks for LLM
  applications and ordinary API security?
- **Considered:** the OWASP Top 10 for LLM Applications (2025 edition) plus
  API security. Covered by existing decisions: sensitive information
  disclosure, data and model poisoning, excessive agency, system prompt
  leakage, vector and embedding weaknesses, misinformation. Five gaps found.
- **Decision & rationale:** Best practice and sensible defaults (Sam):
  1. **Stored prompt injection through summaries (LLM01):** the compaction
     instructions record what the user asked as reported speech ("the user
     asked Capper to..."), never as instructions; summaries sit in the data
     block like other stored user text (code standard 4.6).
  2. **Dependency vulnerabilities (LLM03):** `pip-audit` joins the dev tools
     and runs alongside the specs; CI is a design note.
  3. **Markdown output (LLM05):** the API contract states text parts are
     Markdown to be rendered without raw HTML; the demo page escapes HTML
     before rendering (code standard 6.7).
  4. **Spend over time (LLM10):** design only for the MVP (authenticated demo
     users). Production adds gateway rate limiting and a per-user daily spend
     cap (the Harness's `spend_limits` is a candidate). A presentation note.
  5. **Cross-origin access:** the demo page is served by the same app, so no
     cross-origin access is needed; if it moves, an explicit allowlist.
- **Status:** Decided (Sam, 2026-11-17). Settles T13. A 2026 edition of the
  OWASP list is reported; check it before the presentation (summary-notes.md).

---

## D-078 — Scope model: one app, two buckets, Dockerized
- **Question:** How is scope organized now that design is done?
- **Considered:** three buckets (MVP to build; "plan", designed but not
  built; summary notes) vs. two.
- **Decision & rationale:** We design (full design documentation) and build
  (a working MVP) one app; everything else is set aside for future
  consideration (Sam).
  1. **Two buckets only:** the MVP (`mvp-plan.md`, formerly `open-tasks.md`)
     and future considerations (`future-considerations.md`, formerly
     `summary-notes.md`).
  2. **The "plan" bucket is merged into the MVP list.** Items earlier marked
     "design only" are now MVP candidates; Sam sorts every item into keep or
     punt, and punted items move to future considerations.
  3. **"Too much for manual review" no longer limits the MVP.**
  4. **The service is Dockerized**, at the top of the MVP plan (environment
     details later). This replaces the earlier "no Docker for the MVP".
- **Status:** Decided (Sam, 2026-11-17). Reframes the "design only" labels in
  D-054, D-061, D-064, D-066, D-073, D-075 and D-077 as keep/punt candidates
  until Sam sorts them.

---

## D-079 — One observability solution: OpenTelemetry traces in a local viewer (Q1)
- **Question:** Do we build tracing in the MVP, or keep debugging to logs?
- **Considered:** logs only; Pydantic AI's OpenTelemetry instrumentation
  printed to the console; the same exported to a local trace viewer running
  in Docker; a hosted product.
- **Decision & rationale:** One logging and tracing solution, clean and
  simple for the MVP (Sam): option 3.
  1. Pydantic AI's built-in OpenTelemetry instrumentation: agent runs, model
     calls and tool calls become spans. **Message content capture is off**
     (`include_content=False`, code standard 5.2).
  2. Spans are exported over OTLP to a trace viewer container (e.g. Jaeger's
     all-in-one image) running next to the service in Docker.
  3. **The trace is the single place to debug a turn:** the step-by-step
     detail from D-064 (token counts and budget usage per model call,
     clearing and compaction events, tool calls, retries, errors) is recorded
     as span attributes and events, and the per-turn summary from D-075
     (tokens, cached tokens, estimated cost, time to first token, tool-call
     count, compaction, status) is recorded on the turn's root span. Plain
     stdout logging is kept to startup and unexpected errors.
  4. FastAPI request spans can be added later.
- **Status:** Decided (Sam, 2026-11-17). Supersedes the logging mechanism in
  D-064 point 2 and D-075 point 1 (what is recorded is unchanged); D-075's
  "tracing is design only" no longer applies.

---

## D-080 — Paging list tools for the model; REST list paging punted (Q2)
- **Question:** When a list is longer than one page, can Capper (or the app)
  get the rest?
- **Considered:** `limit` and `total_count` only (built); plus cursor paging
  on list tools; plus paging long lists through REST for the app.
- **Decision & rationale:** Option 2 (Sam). Every list tool returns
  `items`, `total_count` and an opaque `next_cursor` (keyset paging over a
  stable sort, so it stays correct when rows are added); the model passes the
  cursor back for the next page, and a missing cursor means the end. REST
  list paging for the app is punted (it needs app UI).

  Sam's requirement: **tool results must never be truncated in a way that
  misrepresents them.** Best practice (Anthropic's tool-writing guidance;
  the MCP pagination spec; the Harness's tool output limits) is paging,
  filtering and explicit limits with sensible defaults, where any limit is
  stated to the model along with how to get more. A design note for the tool
  result size contract is on `mvp-plan.md` #34 (and #24).
- **Status:** Decided (Sam, 2026-11-17). Refines D-043 and D-064.

---

## D-081 — Memory-pressure warning and pre-compaction extraction punted (Q3)
- **Question:** Should Capper get a warning as its context fills, and should
  key facts be extracted before old turns are compacted (the MemGPT pattern)?
- **Considered:** punting; building the warning only; building both.
- **Decision & rationale:** Punt (Sam). The structured summary (D-043),
  history search (D-074) and guidance notes (D-051) already cover what the
  warning protects, and both variants would conflict with D-051 (save only
  clear requests; no background extraction in the MVP). It stays a
  presentation talking point.
- **Status:** Decided (Sam, 2026-11-17).

---

## D-082 — Resumable streams punted (Q4)
- **Question:** When the app loses its connection mid-reply, can it reconnect
  and watch the rest arrive live?
- **Considered:** check and reload (already in the MVP); resume from memory
  (single instance only); resume from a shared store such as Redis.
- **Decision & rationale:** Punt to future considerations (Sam). The MVP keeps
  check and reload, which is already correct (D-046, D-063); the two ways to
  add live resume are noted in `future-considerations.md`.
- **Status:** Decided (Sam, 2026-11-17).

---

## D-083 — Production content pipeline punted (Q5)
- **Question:** Does the MVP build more than ingestion for knowledge-base
  updates: staged (inactive) content, an eval check before activation, an
  automatic trigger?
- **Considered:** nothing more (ingestion writes active rows, D-050); staged
  content with an activation command; that plus an upload trigger.
- **Decision & rationale:** Punt to future considerations (Sam). The MVP's
  ingestion already handles knowledge-base changes live with no deploy, which
  answers the brief; staging, eval gating and triggers are noted in
  `future-considerations.md`.
- **Status:** Decided (Sam, 2026-11-17).

---

## D-084 — Conversation sessions punted (Q6)
- **Question:** Does the MVP need the server to know when a user's session
  starts and ends?
- **Considered:** no session concept in our service (D-060); reading the
  identity provider's session claims (`auth_time`, `sid`) from the token.
  Neither stores a session: the existing auth API is the only source of truth
  for login sessions, and our service is a stateless resource server (D-020),
  which is microservice best practice.
- **Decision & rationale:** Punt conversation sessions to future
  considerations (Sam). Nothing kept in the MVP needs them.
- **Status:** Decided (Sam, 2026-11-17).

---

## D-085 — Deployment design document punted and merged (Q7)
- **Question:** Is the MVP's "Deployment design (doc)" item redundant?
- **Considered:** keeping it as an MVP document (it would describe a
  deployment we don't build, the "design only" tier D-078 removed); punting it
  into the existing deployment note.
- **Decision & rationale:** Punt and merge with the related item in future
  considerations (Sam): the deployment note (punted #43) now also holds the
  deployment design. Running the Docker image locally is documented with the
  Docker item (#1) in the README.
- **Status:** Decided (Sam, 2026-11-17).

---

## D-086 — Confirmation flow punted
- **Question:** The confirmation flow (D-073) was kept in the sort, but no MVP
  tool needs the user's approval. Build it anyway?
- **Considered:** punting it; making an existing tool require approval
  (reverses D-051's remember-and-tell for memory writes); building it and
  exercising it only in specs with an injected test tool.
- **Decision & rationale:** Punt to future considerations (Sam). Nothing in the
  MVP would use it (D-054), and building unused infrastructure would be the
  "design only" tier in disguise. D-073's design is kept as the note.
- **Status:** Decided (Sam, 2026-11-17). Reverses the keep on mvp-plan #31.

---

## D-087 — Build-time checks settled from the installed source
- **Question:** The four checks recorded for the build (Harness clearing and
  the current turn; Harness spill storage; `store: false` with reasoning;
  Pydantic AI 2.69 API names): what does the pinned source actually do?
- **Considered:** reading the installed packages (`pydantic-ai-slim` 2.69,
  `pydantic-ai-harness` 0.69) instead of deferring to the build.
- **Decision & rationale:**
  1. **Harness `ClearToolResults`** keeps the last `keep_pairs` tool pairs
     counted across the whole history, not per turn. D-065 is met by
     configuration: `keep_pairs` = the per-turn tool-call limit + 5, so the
     current turn is never cleared and at least 5 completed-turn results
     stay. Cleared results keep their tool call (name and arguments), so the
     model can re-run the tool; `min_clear_tokens` avoids clearing for a
     trivial gain (each clear costs one cache miss).
  2. **`store: false` with reasoning:** Pydantic AI requests
     `reasoning.encrypted_content` and round-trips it in history, so
     reasoning flows within a tool-calling turn. Because clearing and
     compaction rewrite history, `openai_send_reasoning_ids` is set to
     `False`, as Pydantic AI's own docs advise when a history processor
     changes messages.
  3. **API names in 2.69:** history processing is the `ProcessHistory`
     capability (there is no `history_processors=` argument);
     `openai_reasoning_context`, `openai_prompt_cache_key` and `openai_store`
     exist as expected; tracing is the `Instrumentation` capability.
  4. **Harness spill storage** writes to a workspace or local files and isn't
     scoped per user, and the Harness also ships its own compaction
     strategies. Both raise MVP questions (mvp-plan #24 and #23).
- **Status:** Decided (verified 2026-11-17). Refines D-052, D-064, D-065.

---

## D-088 — Oversized tool output: limits enforced in our tools; Harness spill punted (Q-A)
- **Question:** Keep the Harness spill for oversized tool results (#24)?
- **Considered:** keeping it with a database-backed, per-user store we write
  (the Harness store protocol gets no user context); dropping it and
  enforcing limits in our own tools.
- **Decision & rationale:** Drop the spill (Sam). Every Capper tool is ours and
  bounded: lists page and state totals (D-080), documents and history snippets
  are small. Each tool result also has a hard size cap; a result that hits it
  returns an explicit "result too large, narrow the request" to the model.
  Never silent, no file storage, no per-user scoping problem. The spill
  matters for unbounded tools (file or web reads), which Capper doesn't have;
  it moves to future considerations.
- **Status:** Decided (Sam, 2026-11-17). Supersedes the "oversized output via
  the Harness" part of D-064.

## D-089 — Compaction built on the Harness (Q-B)
- **Question:** Build compaction ourselves (D-043, D-064), or use the Harness's
  compaction strategies?
- **Considered:** our own summaries logic, watermark selection and background
  job; the Harness's `ClearToolResults`, `SummarizingCompaction`,
  `TieredCompaction`, experimental background start and `ReportContextUsage`.
- **Decision & rationale:** Use the Harness (Sam), leaning on the framework:
  1. **Tiers:** `ClearToolResults` (configured per D-087) first, then
     `SummarizingCompaction` on the compaction model (`gpt-6-luna`, D-047),
     with our structured summary prompt (including D-077's reported-speech
     rule) and retention by tokens (`keep_tokens`), tool calls and results
     kept together.
  2. **Background:** the Harness's background start prepares the summary
     before it's due (experimental; if it misbehaves, compaction still runs
     before the request). The app's shutdown calls the capability's
     `aclose()`, so the background work is owned and awaited (code standard
     6.6).
  3. **Budget reporting:** `ReportContextUsage` feeds the budget numbers onto
     the trace (D-079).
  4. **Persistence stays ours:** when a run compacts, the summary and its
     watermark are saved to the `summaries` table (D-071), so the next turn
     loads them.
  5. **No silent fallback:** the Harness's sliding-window fallback drops
     messages, so it isn't used; if compaction fails, the turn fails with the
     generic error (D-043, D-061).

  Trade-offs accepted: retention keeps whole messages with their tool pairs
  rather than our own turn units; the background start is experimental; the
  dependency on a churning library deepens (talking point in
  future-considerations.md).
- **Status:** Decided (Sam, 2026-11-17). Supersedes the custom compaction
  mechanism in D-043 and D-064 (the goals and limits stand) and the
  lifespan-owned compaction job in D-072.

---

## D-090 — Contract reconciliation after the documentation review
- **Question:** A separate review compared `mvp-plan.md`, this log and
  `future-considerations.md` ahead of the authoritative implementation plan.
  Which contracts need reconciling?
- **Considered:** the review's findings; Claude agreed with all of them, and
  Sam asked for agreed suggestions to be implemented.
- **Decision & rationale:**
  1. **Compaction boundary (D-071, D-089).** The Harness cuts at model-message
     boundaries (tool pairs intact), not at turns, so the watermark records
     the exact message: `summaries.covers_through_model_message_id`, the last
     `model_messages` row the summary replaces. Reload = the latest summary
     plus every `model_messages` row after the watermark, in order. When a run
     compacts, its history is the summary followed by a verbatim suffix; the
     watermark is the last stored message not in that suffix. The 75% trigger
     is enforced (the Harness token trigger); ~40% is a tuning target
     expressed through `keep_tokens`. A deterministic spec covers reload.
  2. **Tool-result retention wording (D-065, D-087).** Clearing protects the
     whole active turn and **at least** the five most recent past-turn
     results (`keep_pairs` = per-turn limit + 5). Cleared originals stay in
     the persisted `model_messages`, but the model has no lookup for them, so
     re-running a tool is a **fresh read** that may return different records;
     "restorable" means the call is visible and can be repeated.
  3. **Send, Stop and errors (D-046, D-061, D-063).**
     1. **Durability:** the turn row and the user's message are committed in
        one transaction before generation starts. On startup, any turn still
        `in_progress` is marked `error`, so a crash can't hold the
        one-active-turn lock forever.
     2. **Duplicate sends:** the same `Idempotency-Key` with the same text
        returns 409 `turn_in_progress` (with the turn ID) while that turn is
        running, and 200 with the stored turn replayed as a short NDJSON
        stream (`turn.start`, the stored parts, `turn.end`, no model call)
        once it has ended. The same key with different text returns 422
        `idempotency_key_reused`. Keys are scoped per user.
     3. **Stop is bound to a turn:** `POST /v1/conversation/turns/{turn_id}/stop`
        (the ID comes from `turn.start`), scoped to the user (another user's
        turn is a 404); stopping a turn that has ended returns 202 with
        nothing to stop. This replaces D-046's untargeted endpoint, which a
        retried old request could use to stop a newer turn.
     4. **Retries:** bounded SDK retries of individual model requests before
        that request's first token; never an automatic replay of the agent
        turn, since tools may already have written data or emitted cards.
     5. **Error channels:** before the stream starts, failures are an HTTP
        status with the JSON error body (401, 404, 409, 422); once the 200
        response has begun streaming, a failure is one terminal `error`
        event, the stream ends, and the turn's status is `error`.
  4. **Safety-net ordering (mvp-plan #40).** The check runs concurrently with
     context building and is awaited **before the first model request** of
     the turn (configurable timeout, default 2 seconds). A flagged policy is
     added from the turn's content snapshot to that turn's per-user context.
     On failure or timeout the turn proceeds without it (fail open), recorded
     on the trace; the always-on do-no-harm core still applies. Policy areas
     are the on-demand policy documents listed in content (D-057).
  5. **Catalog and popular products (R-06, D-070).** The supplied and seeded
     catalog **is** the participating catalog, so no participation field is
     needed. `get_popular_products` returns aggregate rankings only (no other
     users' identities or purchases), excludes the user's avoided products,
     and its basis is "popular at your school" or "popular overall"; "near
     the user" was inaccurate.
  6. **History search (D-074, D-080).** A bounded top-5 relevance lookup over
     message text, exempt from the cursor contract (which applies to tools
     that enumerate records). Card payloads aren't indexed, so "full history
     lookup" means message text; it can't recover which cards were shown.
  7. **Content snapshot (D-050, D-071).** A turn loads the active content set
     once; `read_document` and the safety check use that same snapshot even
     if ingestion publishes mid-turn. Published text is immutable; publishing
     inserts new rows and clears the previous rows' `active` flag in the same
     transaction (the only update allowed).
  8. **Specs (D-062).** A deterministic compaction-persistence spec: the
     transcript is untouched, reload yields the summary plus exactly the
     remaining messages, and tool pairs stay intact. The commented-out judge
     eval is labeled as an example, not an executed quality check.
- **Status:** Decided (Sam, 2026-11-17, via the review). Supersedes D-046's
  untargeted Stop, D-071's turn-level watermark, D-070's "near the user"
  wording and D-074's place under the cursor contract; clarifies D-050,
  D-061, D-063, D-065, D-087 and D-089.

---

## D-091 — Compaction summary format: fixed template with required headings
- **Question:** D-043 asked for a codified summary, not free-form; the
  Harness summarizer writes free text under section headings and checks only
  that it isn't empty. Which format do we validate?
- **Considered:** the Harness summarizer with our own fixed template plus a
  heading check before saving; our own summarizing step with a Pydantic
  output schema.
- **Decision & rationale:** Keep the built-in Harness summarizer, because the
  summary is only context for the next model call (Sam). Our summary prompt
  is a fixed template with required headings (the goals and constraints the
  user stated, IDs mentioned, open questions, with requests recorded as
  reported speech per D-077). The persistence step checks the required
  headings are present before saving and fails visibly if not. **If app code
  ever needs to read individual fields of the summary, switch to a Pydantic
  schema instead.** No MVP code reads summary fields today. The template is
  content, like other prompts (code standard 4.1).
- **Status:** Decided (Sam, 2026-11-17). Amends D-043's "structured schema"
  clause (noted in D-043's body by Sam's direction); refines D-089.

---

## D-092 — TDD review reconciliation (request-only context, compaction by position, turn outcomes, clean-checkout sequence)
- **Question:** An independent review of `mvp-technical-design-document.md`
  found gaps where the TDD contradicted the decisions or the installed
  libraries. Which findings hold, and how is each resolved?
- **Considered:** each finding checked against the decision log and the
  installed Pydantic AI 2.69 / Harness 0.69 source. Most held; three were
  narrowed (below).
- **Decision & rationale:**
  1. **Request-only context (refines D-089, D-090 §4).** Account context and
     the turn context (local time, any flagged policy) are injected by the
     last capability, after clearing and compaction, into the outgoing
     request only. They never enter run history, so they are never persisted
     or summarized. The Harness summarizer runs with
     `preserve_first_user_message=False` and `keep_user_messages=False`
     (its default would have pinned the account block forever). A flagged
     policy goes in the turn context, as D-090 said, not in the
     instructions.
  2. **Compaction by position (refines D-090 §1).** The watermark is computed
     by message position (`[summary] + suffix`), never by comparing payloads;
     the loaded history may start with the previous summary, which a later
     compaction folds in. The heading check (D-091) is an output validator on
     the summarizer, so a bad summary is retried and then fails before it is
     applied. No tiered `skip_on` (it would swallow a failed summary). Each
     run's `conversation_id` is the user's opaque key, so the Harness's held
     background compaction can't cross users. A compact → persist → reload →
     compact spec is added.
  3. **Over the model's limit.** The review asked for a whole-request
     pre-send estimator. Narrowed: OpenAI truncation stays disabled, so an
     over-limit request is rejected by the provider and becomes the generic
     error; nothing is silently truncated. No app-side estimator is built.
  4. **Turn outcomes (refines D-090 §3).** One table governs the live stream,
     what is saved, and replay for `complete`, `stopped` and `error`; an
     assistant message exists only if parts were produced; the user prompt
     is stored in the model history at turn start; the turn commits before
     the terminal event.
  5. **Clean-checkout sequence (D-085, mvp-plan #1).** The service only
     migrates and recovers stale turns at startup; data initialization is an
     explicit sequence (copy the supplied fixture, create keys, migrate,
     seed, ingest, start), documented and used as the Docker check.
  6. **Tool contracts (refines D-080, D-090 §7).** `read_document.name` is a
     string validated against the snapshot (definitions never change per
     request); 14 tools, listed by name; `get_popular_products` follows the
     cursor contract; every list has a deterministic keyset order. Calls past
     the per-turn limit in a batch get the limit result, the next request
     has tool use disabled, and a model-request backstop ends the turn.
  7. **Provenance (refines D-050, code standard 4.4).** The content version
     covers each document's name, class, load and hash; turns also record an
     `app_version` for prompt text that lives in code.
  8. **Control user (D-017).** The TDD had left the legacy history unread,
     which silently dropped D-017's experiment. The seed copies the control
     user's legacy rows into their transcript and model history.
  9. **Smaller fixes:** the eval composes the agent without the safety check
     by dependency injection (no production switch, D-007); a small
     Markdown subset for the demo; the build-time verification policy (only
     a failure that changes agreed behavior is raised).
  10. **Not taken:** a deterministic spec of the model saying "showing N of
      M" (model wording is an eval case, not a spec; the spec checks the
      tool output and description); removing the demo's pasted token (it
      uses the one bearer path; the later "demo convenience" is a separate
      item).
- **Status:** Decided (Claude, 2026-11-17, applying the review at Sam's
  request; item 8 flagged for Sam's confirmation). Refines D-050, D-080,
  D-089 and D-090; honors D-017.
- **Walkthrough with Sam (2026-11-17):**
  1. Item 1 confirmed. Sam's principle: readily available context (account
     data) is never duplicated into conversation history; it goes with each
     request. It is sent on every model request, because D-058 makes it
     always-on context, not a tool. Sam delegated the remaining details to
     common sense and best practice.
  2. Item 2 confirmed. Sam: we never estimate request size before sending;
     it adds complexity and fragility. Caps on inputs plus the provider's
     own rejection (truncation off) are the guard.
  3. Item 3 decided by Claude on best practice (Sam's delegation): as
     applied, except that interrupted tool calls in a stopped or errored
     turn are closed with a synthetic "not run" result instead of dropping
     the trailing model response. Nothing the model produced is lost, the
     stored history stays valid, and the next run sees what was
     interrupted.
  4. Items 4 (clean-checkout sequence), 5 (safety placement, `read_document`
     schema, EVAL-1 isolation), 6 (tool-call cap, 14 tools), 8 (content
     version, `app_version`) and the smaller repairs (item 9 above) decided
     as applied: the findings were valid, and the fixes follow the settled
     decisions and best practice, with nothing left open.
  5. Item 7 pushback confirmed by Sam: "showing N of M" is model wording, so
     it is checked in the eval, not a deterministic spec; the spec checks
     the totals in the tool output and the tool description.
  6. Item 9 replaced by Sam's decision. The pasted token was Claude's own
     default with no decision behind it, so the pushback was withdrawn. Sam:
     login is entirely separate, done by the app's auth API and login portal,
     and not specific to the chatbot; Capper needs only the result, an
     authenticated session used as production would use it (loading the
     user's account and records). Because the brief's auth API is
     hypothetical, the demo page lists the users in the database; clicking
     one creates the session. No simulated login, no stubbed API, no
     separate service. This is the one exception to "no test modes" (D-007,
     code standards 1.1 and 1.3). Built as two Capper routes
     (`GET /demo/users`, `POST /demo/sessions`) that issue an ordinary
     signed token; every other request verifies it through the normal
     D-020 path. `scripts/mint_token` is dropped (tests mint tokens in
     fixtures), and `scripts/init` creates the dev key pair.
  7. Item 8 reversed by Sam: drop the control user, the legacy
     `Conversation_History` table, and anything put in place to support
     them. The migration drops the table (the downgrade recreates it empty);
     the seed step and its spec are removed. Retires D-017's control-user
     experiment. Off-persona history, if ever wanted, is seeded into a user
     through Capper's own tables, like any other conversation (Sam).
  8. The walkthrough is complete; every item is settled.

---

## D-093 — Requirements, defaults and examples are kept distinct
- **Question:** Examples from the mockups, decisions and reviews kept
  becoming build directives, acceptance criteria and prompt rules without a
  decision behind them. How does a fresh build session tell them apart?
- **Considered:** listing the offending examples (rejected by Sam: the list
  itself would travel forward as a checklist); a standing rule plus grooming
  the canonical docs and memory.
- **Decision & rationale:** Standing rule (Sam): **build directives come from
  current approved decisions and requirements. Examples illustrate those
  requirements. Carry forward the underlying rule, and bring in the example
  only when the task specifically needs it.**
  1. The TDD states that rule (§0 item 7); every requirement cites its
     authority; only wording a decision fixes is quoted as required.
  2. The decision-log header says how to read entries: the decision, as
     amended by what its index row points to, is the directive; examples in
     bodies illustrate it.
  3. Examples stay only with a concrete purpose (source material, test
     fixtures, labeled walkthroughs). They were removed from normative text
     in the TDD, `mvp-plan.md` and code standard 7.3, and from persistent
     memory.
- **Status:** Decided (Sam, 2026-11-17). Generalizes D-057.

---

## D-094 — A fully Dockerized product: named volume, init service, health check
- **Question:** A new user who pulls the repo faces a seven-step, order-dependent
  first run, a host-bound `./var` directory for app state (with the container
  user's UID tied to the host), and a reset that means deleting that directory.
  Is that the deployment we want?
- **Considered:** the explicit command sequence (D-092 item 5) vs. a
  production-like Compose setup: a named volume for data, a one-shot `init`
  service that bootstraps idempotently, and a health-checked service.
- **Decision & rationale (Sam):** Capper is a clean, fully Dockerized product.
  We don't run it without Docker. Clear out the stale environment and build
  logic that came from the earlier spike and the "var" workaround.
  1. **The database lives in Docker:** a named volume, not a host directory.
     Reset is `docker compose down -v`.
  2. **An `init` service** runs one idempotent bootstrap before the service
     starts: dev keys, the supplied database, migrations, seed data, content.
     The service waits for it to succeed, then only serves (plus recovering
     interrupted turns at startup).
  3. **A health endpoint** and a Compose health check.
  4. The first run is `cp .env.example .env`, set two values,
     `docker compose up`.
  5. Specs, checks and evals run in Docker too, from a dev image target, so
     nothing needs a local Python setup.
  6. **Everything the MVP uses ships inside the image:** content, product
     images, files, and anything added later. Nothing is fetched from an
     external host or mounted from the host at runtime. Edited content is
     published with a rebuild of `init`, without restarting the service.
- **Status:** Decided (Sam, 2026-11-17). Supersedes D-092 item 5 (the explicit
  first-run sequence) and the TDD's ENV-8 ("the service never initializes
  data"), which Sam judged had leaked in. Item 6 is Sam's answer to the
  content question (baked in, not mounted).

---

## D-095 — Interrupted tool calls are closed by the framework, not in stored history
- **Question:** API-14 says a tool call left without a result in a stopped or
  errored turn is stored with a synthetic "not run" result. The build stores
  the history as it happened, and Pydantic AI closes the call with an
  interrupted result when the history is next sent. A spec that stops a turn
  mid-tool confirmed this. Change the code, or the wording?
- **Considered:** write our own synthetic result into stored history at turn
  end; or keep the framework's behavior and correct API-14.
- **Decision & rationale:** Keep the framework's behavior and correct API-14.
  The next request is valid and shows the model what was interrupted, with no
  code of ours; code standard 6.2 already says the next message continues
  "using Pydantic AI's built-in handling, with no custom history filtering or
  repair". Writing our own result would add code and duplicate the
  framework's.
- **Status:** Decided (Claude, on Sam's instruction to use common sense and
  best practice for minimal complexity, 2026-11-18). Supersedes D-092's
  synthetic "not run" result for interrupted tool calls. Closes discussion
  item 4.

---

## D-096 — Compaction runs inline; the background start is removed
- **Question:** A spec showed that a summary the Harness prepares in the
  background (from 80% of the trigger) is never used. The run stamps the
  turn's prompt after the Harness's snapshot, and the stored prompt never gets
  those stamps, so the history never matches and every prepared summary is
  discarded; compaction then runs inline. In a 14-turn spec, about 10
  background summaries were written and thrown away for one used. Fix it, or
  remove it?
- **Considered:** make it match (rewrite the stored prompt at turn end, and
  work around the framework's stamping within a turn); or remove the
  background start.
- **Decision & rationale:** Remove it (Sam). Inline compaction works and is
  proven by the specs; the background start saved no latency and spent a
  model call each time. With it go the `compaction_background_start`
  setting, the single-strategy `FallbackCompaction` wrapper (the summarizer
  has its own token trigger), and the shutdown `aclose()` that existed only
  for background work (CMP-9). A working head start is a future
  consideration.
- **Status:** Decided (Sam, 2026-11-18). Supersedes D-089 item 2. Closes
  discussion item 11.

---

## D-097 — Post-MVP cleanup: the implementation choices
- **Question:** `docs/post-mvp-cleanup.md` lists the agreed cleanup (items 1,
  3, 5, 7, 12, 13, 16, 19, 27, 31 and 36). Where it leaves a detail open,
  what does the build do?
- **Decision & rationale:** Best practice, recorded here (Claude):
  1. **Safety check removed (item 1).** Turns go straight to the chat model
     once context is loaded; the always-on core and `read_document` remain.
     Its prompt was dropped from the manifest, so the next publish
     deactivated it (verified on the demo volume).
  2. **The avoid list (item 27)** is no longer in the account context. Adding
     and removing match by name: an exact name wins, otherwise names
     containing the text; several matches change nothing and come back as
     an error listing them, so the model asks. Removal by product ID stays. A
     read-only `get_my_avoid_list` tool was added, because without the list in
     context the user could no longer review it (code standard 3.3); its
     description says to name avoided products in text, since cards refuse
     them. The `product_name` argument is redacted in the audit, like other
     user words.
  3. **Time zone (item 36)** is a nullable `Users.time_zone` column added by
     migration `0002`. An unknown stored zone falls back to the default with
     a warning; an invalid configured default fails at startup.
  4. **History by date (item 5)** takes `start_date` and `end_date`, both
     included and both required together; the tool returns times in the
     user's zone.
  5. **Failures (item 19)** are recorded as `error.type` (`context_limit`,
     `model_api_error`, `usage_limit`, `timeout`, or the exception's class
     name), with the provider's machine-readable code and HTTP status. A
     provider error is logged by category only, without its message.
  6. **Tracing (items 12, 16)** dropped `capper.app_version` (it repeated the
     resource's `service.version`), the `context.clearing` event (it repeated
     `capper.cleared`) and the `context.compaction` event for turns that didn't
     compact. It added `context.summary_loaded` and `context.summary_saved`.
  7. **Limits (item 13)** keep their defaults; a spec now covers the turn
     timeout. **Confirmation (item 31):** nothing in the code existed only for
     it, so nothing was removed.
- **Status:** Decided (2026-11-18). Supersedes D-090's safety check (SAFE-1
  to SAFE-3) and D-051's avoid list in the account context.

---

## D-098 — One initial migration and minimal Alembic setup
- **Question:** What migration setup does this unreleased, one-off MVP need?
- **Considered:** retaining two revisions and offline SQL-generation setup;
  combining the schema changes and keeping only the execution path used by bootstrap.
- **Decision & rationale:** Combine the time-zone change into `0001_initial.py`
  and remove `0002`. Simplify `env.py` to connect and run migrations, removing
  the offline branch and unused `render_as_batch` settings. Keep Alembic's
  standard `script.py.mako` template. Existing demo databases at `0002` need
  their revision reconciled once; new databases use the combined migration.
- **Status:** Decided (Sam, 2026-11-18). Supersedes D-097 item 3's separate
  migration `0002`; the time-zone behavior is unchanged.

---

## Open questions

None. Q1–Q8 (2026-11-16) and W1–W14 plus the design tasks (2026-11-17) are
all settled: Q1 → D-044, Q2 → D-047, Q3 → D-043, Q4 → D-049, Q5 → D-050,
Q6 → D-051, Q7 → D-045, Q8 → D-046; W1–W14 → D-056 to D-070; T16 → D-071,
T1 → D-072, T3 → D-073, T5 → D-074, T7 → D-075, T8 → D-076, T13 → D-077.
Remaining work lives in `mvp-plan.md`; everything else is in
`future-considerations.md`.

## Retired open items

P-001→D-004/D-016 · P-002→D-041 · P-003→D-010 · P-004→Q1 · P-005→D-019 ·
P-006→D-036 · P-007→summary-notes · P-008→interviewer · P-009→Q3 ·
P-010→Q2 · P-011→open-tasks T1 · P-012→Q4 (all in open-tasks.md; Q1–Q8 now
settled as above)
