# Features

Capper is a working proof of concept for an in-app Carton Caps assistant.
It focuses on product discovery, referral support, and maintaining useful
context across a continuing conversation. [Known limitations](known-limitations.md)
describes its gaps.

Each feature includes its origin:

- **Brief (written):** explicitly requested in the written challenge or based
  on the supplied business reference documents.
- **Brief (mockups):** behavior shown in the supplied UI screenshots. Page
  numbers refer to the PDF's pages, counted from the first page.
- **Added:** functionality or an engineering choice introduced beyond the
  supplied requirements. This includes the specific implementation chosen
  to support a requested behavior.

The sources are the [written challenge](challenge-criteria.md), the
[UI mockups](<../supporting-files/Livefront Engineering Challenge UI Design (AI).pdf>),
the [Referral FAQ](<../supporting-files/Carton Caps Referral FAQs.pdf>), and the
[Program Rules](<../supporting-files/Carton Caps Referral Program Rules.pdf>).
A mockup establishes the illustrated behavior; it does not prescribe the
backend mechanism. Where those origins differ, both are identified below.

## Product discovery and referral support

- **Personalized product recommendations — Brief (written).** The challenge
  asks for recommendations using user context. The product flow also shows
  asking clarifying questions and carrying preferences across turns
  (**Brief, mockups p. 3**).
- **Catalog and purchase-history lookup tools — Added.** Search by product
  name or description, browse without a search term, and retrieve the user's
  purchases. These tools implement the requested personalization using the
  supplied data model; the brief does not specify their interfaces or search
  algorithm.
- **School and overall popularity rankings — Added.** Find popular products
  at the user's school, with an overall fallback when no school is linked.
  This gives the assistant a starting point when personal context is thin.
- **Current Bonus Caps promotions — Brief (mockups p. 3).** The product flow
  asks about current bonuses and shows promotion cards. Time-filtered promotion
  lookups and seeded promotion records are **Added** implementation choices.
- **Card presentation — Brief (mockups p. 3), extended.** The screenshots
  show a promotion carousel with images and titles. Product cards, displayed
  prices, the cards-only product-presentation rule, and building all card
  contents from database records are **Added** choices.
- **Referral explanations and troubleshooting — Brief (written and mockups
  p. 6).** Explain program rules and steps, clarify the user's problem, adapt
  instructions to the situation, and retrieve the user's own referral code.
  The FAQ and Program Rules supply the business reference material; the mockup
  explicitly shows a personal code.
- **General app help and support direction — Brief (mockups pp. 3 and 6),
  extended.** The greeting promises to direct users to someone who can help.
  Curated help-content stubs and the rule to acknowledge missing information
  instead of inventing an answer are **Added** choices. Handoff currently
  means guidance in the reply, not a support-system integration.
- **List totals and pagination — Added.** Lookup results include counts and
  cursors so the assistant can explain partial lists and retrieve more pages.

Recommendations and explanations are model-generated; these origin labels
identify the intended capabilities, not guarantees of answer quality.

## Streaming conversations and demo client

- **Multi-turn conversation API — Brief (written).** The deliverable requires
  an API that creates and maintains conversations using an LLM and user context.
- **Capper greeting and formatted replies — Brief (mockups pp. 3 and 6).**
  The screenshots show the assistant's name, a fixed three-bubble greeting,
  short reply bubbles, lists, headings, and a polite close.
- **Processing state and Stop control — Brief (mockups pp. 4 and 7).** The
  screenshots show processing dots and a send button that becomes a Stop
  control. The turn-specific cancellation API and token registry are **Added**
  implementation choices.
- **NDJSON streaming — Added.** Typed events carry turn start, text, cards,
  completion, and errors. The mockups show a processing state but do not
  explicitly require token streaming or prescribe a wire protocol.
- **Browser demo client — Added, styled from the mockups.** A plain-JavaScript
  page exercises the API, renders streaming text and card carousels, displays
  saved history, and lets reviewers switch between demo accounts. HTML escaping
  and restricted Markdown rendering are **Added** safeguards.
- **Persisted, paginated history — Added implementation.** Maintaining
  conversation context is requested; one continuous conversation per user,
  database persistence, and the transcript-history endpoint are design choices.
- **Partial replies and continuation after Stop — Added.** Save the partial
  reply and interrupted model history, then mark the turn as stopped.
- **Generation survives client disconnects — Added.** A disconnected client
  does not cancel the background run; generation can finish and save its result.
- **Concurrent-turn controls — Added.** Only one turn per user can run at a
  time; different users can have active turns concurrently.
- **Idempotent sends and replay — Added.** A client key identifies an
  intentional send. Retrying it does not start another model run, and a
  completed response can be replayed.
- **Message feedback — Added.** Thumbs up/down rates the quality of the whole
  assistant response, not individual products or recommendation rankings. The
  demo sends a rating; the API also accepts a short comment. Feedback is stored
  for review and does not currently affect recommendations or feed an automated
  evaluation or learning process. The supplied mockups do not show feedback controls.
- **Local timestamps and date handling — Added implementation.** The mockups
  show a conversation timestamp (**Brief, mockups pp. 3 and 6**); account time
  zones and local-calendar-day search semantics go beyond that visual detail.

## Policy handling and scope

- **Purpose and voice instructions — Brief (written and mockups).** The
  written challenge asks how responses stay aligned with the assistant's
  purpose. The screenshots establish the friendly Carton Caps persona and
  context-aware support style. Separate scope and persona documents are an
  **Added** implementation choice.
- **Do-no-harm policy system — Added.** An always-loaded safety core directs
  the agent to read detailed policies for allergies and food safety, dietary
  and medical claims, child safety, product misuse, and crisis or distress.
  The mockup asks about allergies, but the broader policy taxonomy, detailed
  safety rules, and on-demand `read_document` mechanism were introduced for
  this project rather than requested in the brief.
- **Consistent policy snapshot — Added.** Policy reads within a turn use the
  same published content snapshot. Policy selection and compliance in free-text
  answers still depend on the model.
- **Application-enforced tool boundaries — Added.** Strict schemas, verified
  identity, access scoping, tool-call limits, and result-size limits constrain
  tool execution. Product cards reject unknown or avoided products; promotion
  cards also reject inactive promotions.

## Saved guidance and avoided products

- **Durable guidance notes — Added.** Save, update, and remove short notes
  when the user asks to remember something. Notes can expire and appear in
  account context as user data. Remembering preferences within a conversation
  is shown in the mockups; a separately managed, persistent memory system is not.
- **Avoid list — Added.** Add, review, and remove avoided products. Server-side
  catalog queries and card validation enforce exclusions. Ambiguous names
  produce clarification candidates without changing the list.
- **Immediate writes with disclosure — Added.** Writes return the outcome for
  the assistant to disclose, without a separate approval step. Note length,
  note count, and avoid-list size have configured limits.

## Context management and history recall

- **Conversation-context management — Brief (written).** Maintaining multi-turn
  conversation and using preprocessing, prompts, or context management are part
  of the requested prototype. The mechanisms below are **Added** design choices.
- **Separate transcript and model history — Added.** Visible conversation
  records remain intact while the model's working context can change.
- **Request-only account and time context — Added.** Inject current account
  context and local time without repeatedly saving them into model history.
- **Tool-result clearing and compaction — Added.** The Harness clears older
  tool results and summarizes older history using a separately configured
  compaction model, retaining recent messages. The summary template defines
  required headings, which are checked before use.
- **Separate chat and compaction models — Added.** Conversation uses the chat
  model (`gpt-6.1-terra` by default); summarizing older history uses a cheaper
  model (`gpt-6-luna`), at about a tenth of the chat model's input price in
  the configured estimates. Summaries are background work that doesn't need
  the chat model's quality, so long conversations cost less. Each model is a
  setting, so the client can tune cost against quality per job.
- **Persisted summaries and message boundaries — Added.** Later turns reload
  the saved summary and the history after its cutoff consistently. Compaction
  does not delete the visible transcript.
- **Transcript history search — Added.** User-scoped SQLite full-text search
  retrieves bounded snippets by words, local date range, or both. This is
  additional recall machinery beyond maintaining the current conversation.
- **Provider prompt caching — Added.** Stable instructions and an opaque
  per-user cache key support provider prompt caching.

## Versioned content publishing

- **Knowledge-update strategy — Brief (written).** The challenge asks how data
  and knowledge updates would work and explicitly permits documenting the
  approach without implementing it. The publishing pipeline below is **Added**
  working functionality beyond that minimum; see
  [Content and knowledge updates](diagrams/content-updates.md).
- **Authored Markdown and an explicit manifest — Added.** Persona, scope,
  safety policies, business knowledge, greetings, and the compaction template
  are published through an allowlist with defined loading modes.
- **Normalized, versioned publishing — Added.** Ingestion removes authoring
  comments, normalizes whitespace, and hashes bodies. Publishing creates
  immutable body versions and changes activation flags atomically, retaining
  unchanged documents.
- **Updates take effect between turns — Added.** New content is visible on
  the next turn; an active turn keeps its original snapshot.
- **Curated business-document stubs — Added preparation of supplied material.**
  The referral FAQ and Program Rules come from the brief. Converting them to
  Markdown, resolving their conflicts for the demo, and authoring missing app
  help content are project choices that demonstrate an administrator-fed
  publishing workflow.

## JWT verification and user isolation

The written brief assumes authentication and registration already exist and
explicitly excludes designing them. It does not prescribe JWTs or a demo login.

- **Per-request JWT verification — Added.** Protected routes verify RS256
  signatures using a trusted public key, require expiration, issuer, audience,
  and subject claims, and confirm that the user exists.
- **Identity-bound application and tool access — Added.** Verified identity
  scopes transcript, memory, referral-code, feedback, and history operations.
  The model cannot choose another user through a tool argument. Stop and
  feedback also check ownership.
- **Demo token issuer — Added.** Choosing an account issues a signed token
  without a password. Requests use the ordinary verification path, providing
  a stand-in for the hypothetical external identity service. Real login and
  registration remain outside the prototype.

## Observability and verification

- **Unit and integration testing — Brief (written).** Tests of the service and
  conversation logic are an explicit deliverable. Scripted models, tests that
  avoid provider calls, and the particular coverage are **Added** engineering
  choices. Coverage includes user isolation, streaming, Stop and continuation,
  idempotency, publishing, memory limits, compaction persistence, and API schemas.
- **Linting, formatting, and type checking — Added.** Ruff checks lint and
  formatting; Pyright checks type contracts in strict mode.
- **OpenTelemetry traces and local Jaeger viewer — Added.** Turn, model, and
  tool activity includes timing, time to first token, token usage, estimated
  cost, outcomes, and compaction activity. Message-content capture is disabled.
- **Tool-call audit records — Added.** Persist outcomes, latency, and arguments
  with selected free-text fields redacted.
- **Model response-storage opt-out — Added.** Chat and compaction requests
  opt out of OpenAI response storage.
- **Real-model evals — Added.** Check policy-tool choices and use an LLM judge
  for three answer-quality cases. Evals run on a temporary database copy and
  fail if a case or evaluator fails. These extend the required tests; they are
  lightweight checks rather than a calibrated quality benchmark.

## Reproducible local setup

- **Docker Compose packaging — Added.** Run the application and trace viewer
  with a persistent SQLite data volume. The brief requires a working prototype
  but does not prescribe containers, SQLite, or a trace-viewer service.
- **Automatic initialization — Added.** Create demo signing keys, copy the
  supplied database, apply the Alembic migration, seed demo data, and publish
  content before the service starts.
- **Seed data and illustrative images — Added.** Extend the supplied dataset
  so demo users have purchase histories and the mockup-inspired product and
  promotion flows have supporting records and images.
- **Development image — Added.** Package the test, lint, type-check, and eval
  tools with the repository. Setup and run commands are in the
  [README](../README.md).
