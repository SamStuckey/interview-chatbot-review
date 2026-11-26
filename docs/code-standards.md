# Code Standards

## 1. Production code and test code

1. Keep mocks, fakes, and test switches in the test suite. The demo sign-in
   routes are the sole exception. They issue ordinary tokens that every
   authenticated route verifies through the normal path. Do not create
   'fake', 'test', or 'stub' modes in the code. The goal is to make the 
   application layer of this program as production like as possible.
2. Inject external dependencies, including model clients, databases, and
   clocks. Tests supply their own implementations.
3. Keep bootstrap, seeding, and ingestion outside request-handling code.
   Do not expose development tooling through service routes, apart from the
   demo sign-in routes.
4. Noteable exception; this application is an MVP built to demonstrate proof
   of concept. Deployment architecture, testing architecture, and other out
   of scope build points can be built to a bare minimum functional standard,
   and should not be the subject of production code like quality standards. For
   example, we do not care about networking concerns on our docker port
   assignments, as this will only ever run as a demo in it's current
   implementation.

## 2. Identity, authorization, and data access

1. Derive the user identity for authenticated requests and tools from the
   verified token. Never accept a replacement identity from request bodies,
   URL parameters, or model-generated tool arguments.
2. Scope every query for user-owned data by user ID in the data-access layer.
3. Enforce authorization in application code or the downstream system.
   Never rely on prompt instructions for access control.
4. Test cross-account isolation for every endpoint and tool that accesses
   user-owned data.

## 3. Tools

1. Define tools with typed, strict input schemas. Validate required fields,
   reject extra properties, and parse model-generated arguments as structured
   data.
2. Keep tools narrow and task-specific. Grant only the access each tool
   needs; do not expose general-purpose SQL or shell execution.
3. Execute user-requested changes and disclose what changed after they succeed.
   Let users review and remove saved guidance and avoided products.
4. Enforce authorization and limits on every tool execution.
5. Audit tool calls with the user, turn, tool name, redacted arguments,
   outcome, and latency. Audit interrupted and failed executions as errors.
6. Return expected validation and domain errors to the model as tool results.
   Let unexpected failures reach the turn's error handler.

## 4. Prompts and context

1. Author persona, policy, knowledge, and summary templates as content
   documents. Publish them through ingestion and read their database versions.
2. Keep fixed instructions and tool definitions stable across requests.
   Place per-user context and conversation history after the stable content;
   keep timestamps, user names, and request IDs out of fixed instructions.
3. Publish only manifest-listed source documents. Normalize them before
   storing new versions. Never edit published bodies; update activation flags
   atomically when replacing or removing documents.
4. Record the model, content version, and application version on each turn.
   Record the summarizer model, content version, and covered message boundary
   with each saved summary.
5. Access structured application data through database queries and tools.
6. Keep user-derived text out of trusted instructions. Treat saved guidance,
   summaries, and history-search results as untrusted data that cannot change
   identity, permissions, scope, or policy.
7. Build product and promotion cards from database records. Validate IDs,
   eligibility, and avoided products before emitting cards. Ground free-text
   product claims in retrieved data.
8. Read one content snapshot per turn and use it throughout that turn.
   Read live data through tools. Do not cache documents, live data, or model
   answers across requests in the application. Use an opaque per-user key
   for provider prompt caching.

## 5. Conversation data

1. Keep transcript and model-history records append-only. Compaction changes
   the model's working context, not the stored conversation. Persist summaries
   with their covered message boundary so later turns reload consistently.
2. Exclude message bodies, sensitive user data, and secrets from logs and
   traces. Use opaque user keys and record IDs for correlation.

## 6. API and streaming

1. Stream responses as NDJSON events with stable types and payloads for
   turn start, text, cards, completion, and errors.
2. Bind Stop to a specific user-owned turn. Save partial output and interrupted
   model state, and use the framework's continuation handling on the next
   message. A disconnect must not cancel generation. Allow only one active
   turn per user.
3. Keep database transactions short. Never hold a transaction open across a
   model call or response stream. Use async database access in the service.
   Commit the turn's final state before emitting its terminal event.
4. Create one async session per unit of work from a session factory. Use
   `expire_on_commit=False` and explicit relationship loading. Do not retain
   a request-scoped session for the duration of a stream.
5. Raise domain exceptions from services. Map them to HTTP responses in one
   place at the API boundary. Keep HTTP types and status codes out of services
   and repositories. Use a terminal error event for failures after streaming
   begins.
6. Keep blocking work off the event loop. Track background generation tasks
   through the application lifespan and await them on shutdown. Mark orphaned
   active turns as errors at startup. Run compaction inline within the turn
   that needs it.
7. Render Markdown with raw HTML disabled. Escape model-generated HTML before
   rendering it in the demo client.

## 7. Module boundaries

1. Keep ingestion separate from the service. Both depend on the shared
   `content_bundle` contract; neither imports the other's internals.
2. Keep provider-specific SDKs and settings in the provider adapter and
   configuration. Keep business logic independent of provider details.
3. Build generic lookup, display, and memory capabilities. Keep scenario-specific
   instructions in content rather than adding tools, fields, or branches for
   individual examples.
4. Organize code by domain. Keep models, repositories, services, and API
   adapters together where each is needed. Keep files small and cohesive;
   split unrelated responsibilities into separate modules.
5. Keep routes responsible for HTTP, services for use cases, repositories
   for queries, and agent tools for adapting service calls. Keep FastAPI and
   Pydantic AI types out of services and repositories.
6. Read settings and construct dependencies at process entry points. Wire
   service dependencies in the app factory. Do not construct clients or read
   environment settings at module import time in reusable application code.
7. Keep context assembly, budget calculations, summary checks, and card
   construction pure where possible. Keep I/O at the boundaries.

## 8. Style, dependencies, and verification

1. Manage dependencies with uv and commit the lockfile. Pin the Harness
   dependency exactly.
2. Prefer the standard library. Document the purpose of each direct
   third-party dependency in the [developer reference](development.md). Reuse
   existing code and framework functionality before building another implementation.
3. Use descriptive names that make the code's purpose clear. Comments should
   explain constraints, reasoning, and surprising choices rather than repeat
   routine operations. Keep them self-contained; omit planning IDs and
   conversation attribution.
4. Keep the demo client in plain JavaScript with no frontend framework or
   build step.
5. Bound provider retries and timeouts. Retry individual requests only before
   their stream begins; never automatically replay an entire agent turn.
   Surface failed compaction instead of silently truncating history.
6. Trace turn, model, and tool activity with available usage, budget, timing,
   outcome, and compaction metadata. Disable message-content capture. Use
   module-level loggers for startup and errors; keep service code free of
   `print` calls. Do not log provider error text that could echo a request.
7. Annotate functions and run Pyright in strict mode alongside Ruff. Avoid
   `Any` where a concrete type or protocol can express the contract.
8. Mirror the source layout in tests. Test pure functions and services
   directly and API behavior through the test client. Keep tests independent
   of network access. Run real-model evals separately by explicit command.
9. Keep functions short and focused on one clear job. Split distinct operations
   into named helpers when doing so improves readability.
10. Prefer straightforward control flow. Avoid deep nesting and unnecessary
    branching.
11. Add abstractions only when they solve a current problem. Avoid speculative
    frameworks, wrappers, and configuration.
12. Remove unused functions, arguments, imports, settings, and abandoned
    scaffolding.
