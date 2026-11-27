# Study Plan

The canonical list of what we're working through to prepare for the
follow-up interview, where I'll open the editor and work on Capper live.
Capper is the worked example, not the source of truth: invented features are
fine when they demonstrate an idea, and the aim is understanding that holds up
beyond this app.

Build tasks come first and concepts later. Each build task lists the
concepts it covers, so vocabulary is learned while doing the work. Topics
already covered in [the study guide](study-guide.md) are listed at the end and
not repeated.

This plan isn't the only thing we discuss. Other topics come up along the
way, and items move onto this list only once Sam approves them.

## 0. Setup

- **Isolate this clone from the original project.** Both clones use the same
  Compose project name (`name: capper`), image tags (`capper:local`,
  `capper-dev:local`), named volume (`capper_capper-data`) and host ports
  (8000, 16686). Running Docker from this clone would therefore share the
  original's database and signing keys and replace its containers and
  images. Give this clone its own project name and image tags, and never
  modify the original clone. `uv run pytest` is already isolated: each test
  uses a temporary database.

## A. Build: core skills on this app

1. **Change an existing tool end to end.** Add `max_price` to
   `search_products`: the tool's schema and docstring, the service, the
   repository query, and a spec.
2. **Add a new tool.** `RunContext` and deps, the docstring as the model's
   prompt, `strict`, and `ToolGuard`.
3. **Change what the model sees.** Content edits and republishing, adding a
   request-only context block, capabilities and hooks, choosing between
   instructions, per-request context and a tool, and how request order
   affects prompt caching.
4. **Spec + eval for a behavior change.** `ScriptedModel` and `running_app`,
   pytest fixtures, `conftest.py`, `parametrize`, `monkeypatch`, and an eval
   case.

## B. Build: features, most from Known limitations

5. **Favorites: the full new-domain walkthrough.** A migration for a new
   table; models, repository and service; routes; wiring in `create_app`,
   plus a new setting; and an agent tool so Capper can use it. Pairs with
   DDD (14).
6. **Queryable card history** ([Known limitations](known-limitations.md)
   §13: the JSON-column problem). Compare SQLite JSON functions (`json_each`)
   over the existing column, a generated column with an index, and a
   separate `card_impressions` table written in the same transaction as the
   reply. Build the table, a backfill data migration from existing messages,
   and a "most recommended products" query.
7. **Per-user spending limit** (§11). Modify an existing table (token
   columns on `turns`), record usage when a turn ends, and refuse a new turn
   over a daily budget with a new domain error and a 429 response.
   Optionally, split cost per model.
8. **Cards only from real lookups** (§4). Version 1: track the IDs each
   lookup returns within the turn, held in deps, and have `show_products`
   refuse any ID it didn't return. Version 2: persist those lookup results
   so a follow-up in a later turn still works.
9. **Delete my data, plus a retention job** (§9, [Privacy](privacy.md)). An
   erasure service that reaches every stored copy (transcript, search index,
   model history, summaries, tool audit); then a scheduled job that reuses
   it to purge old data. Covers lifespan-owned tasks, `asyncio.create_task`
   and cancellation, and in-process vs separate-process vs production
   schedulers.
10. **Observability and streaming.** A trace attribute, plus a
    "Searching products…" `tool.status` stream event: async generators, the
    event queue, and saving and replaying parts.
11. **Caching.** Why the code standards ban app-side caching and whether
    that's best practice; a TTL cache on popular products with an injected
    clock; the `lru_cache`-on-async gotcha; Redis across instances; and the
    contrast with prompt caching.

## C. Stretch builds

12. **A confirmation flow for action tools** (§10). Pydantic AI's
    `requires_approval`, the pending-action design in D-073, and
    approve/decline endpoints.
13. **Better product search** (§5). An FTS5 index over products with
    ranking, compared with substring search. Embeddings discussed but not
    built.

## D. Concepts (explain out loud, and quizzed)

14. **DDD:** what it is, aggregates, value objects, bounded contexts, and how
    much of it Capper actually uses. Best done alongside task 5.
15. **Context management in depth:** clearing, compaction, the summary
    watermark, and the two conversation records.
16. **Turn lifecycle:** stop vs disconnect, idempotency, and errors at each
    boundary (HTTP error, tool error result, terminal stream event).
17. **Scaling to several instances** (§2): where the in-process stop
    registry and turn tasks break, and what Redis or a managed database
    changes.
18. **LLM fundamentals:** tokens and context windows, the tool-calling loop,
    prompt injection, grounding, and reasoning-model settings.
19. **Python idioms not exercised above:** `Protocol`, generics and `type`
    aliases, `Literal`, the walrus operator, `raise ... from`, keyword-only
    arguments, comprehensions.
20. **Tooling and running:** uv, `pyproject.toml` and `uv.lock`; Docker
    Compose, the data volume, rebuilds, and Compose project names.

## E. Production shortcuts (discuss, and fix where useful)

Places where Capper takes a demo shortcut a production service wouldn't.
Each is a likely interview topic: be ready to say what the shortcut is, why
it's fine for the demo, and what production would do instead. ★ marks
shortcuts that aren't written up anywhere in the docs, so there's no
prepared defense for them yet.

**Identity and secrets**

21. ★ **The API service holds the private signing key.** `create_app` loads
    it for the demo token issuer. A service that only verifies tokens should
    hold just the public key; the private key belongs to the auth service.
22. ★ **`/demo/users` lists every user's name and school with no login.**
    Personal data exposed to anyone, on top of the sign-in bypass. The demo
    routes are always on, with no setting to turn them off.
23. ★ **The public key is read once at startup from a file.** No key IDs
    (`kid`) and no fetching of the auth service's published keys (JWKS), so
    rotating the key needs a restart.
24. **Secrets live in `.env`**, not a secrets manager, and the cache-key
    secret is never rotated.
25. ★ **`/docs` and `/openapi.json` are public** (FastAPI's default).

**Data ownership and the database**

26. ★ **Capper's migration changes and deletes tables in the client's
    database.** It adds columns to `Users` and `Products` and drops
    `Conversation_History`. A service shouldn't migrate another system's
    tables.
27. ★ **The `init` service seeds demo data and copies the fixture database
    on every start.** Demo data is part of the deployment path.
28. **SQLite: one writer at a time, and no backups.** ★ WAL mode, which lets
    reads continue during a write, isn't enabled.

**Running more than one instance, and shutdown**

29. ★ **Startup marks every in-progress turn in the database as failed.**
    With two instances, or during a rolling deploy, a new instance kills
    turns still running on the old one.
30. ★ **Shutdown waits up to the 60-second turn timeout, but Docker's default
    stop grace period is 10 seconds** (`stop_grace_period` isn't set).
    Containers are killed mid-turn, and those turns become errors on the
    next start.
31. **Stop tokens, turn tasks and event queues live in process memory**, so
    a Stop request that reaches another instance does nothing.
32. ★ **A single uvicorn worker, with host and port hardcoded** in
    `__main__.py`.

**Assets and content**

33. ★ **Product images ship inside the app image and are served by the
    app.** A new image needs a rebuild, and `image_url` is derived from the
    product's name, so renaming a product breaks its image. Production
    would use object storage plus a CDN, with the URL stored as data.
34. **Publishing content means rebuilding the `init` image**: no admin
    path, review step or rollback.

**Operations and observability**

35. ★ **Plain-text logs with no request IDs**, so a log line can't be tied
    to its trace.
36. **The health check only tests the database**: no liveness/readiness
    split, and no check that the model provider answers.
37. **Jaeger stores traces in memory**, and its UI has no login.
38. **Only OpenAI is wired up, with no failover.** ★ Model prices are
    hardcoded defaults, and the eval judge model is a constant in code.

**API surface**

39. ★ **Unhandled exceptions return Starlette's plain-text 500**, not the
    JSON error envelope the API contract promises.
40. ★ **No request body size limit.** Message length is checked only after
    the whole JSON body has been read.
41. **No rate limits or spending caps** (task 7 covers part of this).
42. **Some limits are hardcoded rather than settings:** page sizes, the
    200-character idempotency key, the comment length, the 10-item card
    maximum.

## F. Covered in the study guide (refresher quiz only)

Evaluators · async/coroutines · `with` / `async with` · stateless JWT
verification · Ruff · Pyright · async SQLAlchemy sessions

## Dropped, and why

**Merged into other tasks:**

- **The separate migration, routes, wiring and new-domain tasks:** folded
  into Favorites (5), so there's one coherent feature rather than four
  fragments.
- **"Add an eval case" as its own task:** merged into task 4. In practice
  the eval is added when the behavior changes.
- **REST endpoints to manage saved guidance:** a real gap, but Favorites (5)
  and Delete-my-data (9) already cover building routes.
- **A standalone scheduled-job task:** now part of task 9, where the job has
  a real reason to exist.

**Known-limitations sections not turned into builds:**

- **§1, real login integration:** needs an external identity provider;
  nothing meaningful to build locally.
- **§2, multi-instance turn ownership:** mostly infrastructure work. Kept
  as a concept (17).
- **§3, a separate answer-review model:** expensive and judgment-heavy, and
  it mirrors the safety check that was built and then removed. Talking
  point only.
- **§5, embeddings and semantic search:** needs an embedding model and
  storage. FTS5 (13) teaches the same ranking ideas locally.
- **§7, replacing the Harness compaction:** too large. Understanding the
  current pipeline (15) is what matters.
- **§8, ingestion validation and an admin portal:** mostly UI and process
  work, with little backend code to learn from.
- **§12, calibrating the eval judge against human labels:** a data-labeling
  process, not code.
- **§14, client-generated message IDs:** an API contract discussion, covered
  under turn lifecycle (16).
