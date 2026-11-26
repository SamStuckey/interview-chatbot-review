# Capper MVP review: normalized

The agreed refactor of the MVP's code, approved by Sam on 2026-11-18. This
document is the single source for these changes.

**Scope:** the chatbot's code only. Docker configuration, the demo page, the
eval tooling and submission order are out of scope, and so are nits. The code
works; the goal is code that's well written, minimal and readable.

**Baseline:** file and line references are to commit `1dd3c1d` on `build/mvp`.
They drift as items land, so find code by the names given.

Each item gives:
- what's wrong;
- the exact change;
- why.

| # | Change | Area |
|---|---|---|
| 1 | Opt every model request out of OpenAI storage | Privacy |
| 2 | Hide query values from logged errors | Privacy |
| 3 | One paging helper that validates cursors | Correctness and readability |
| 4 | Treat `%` and `_` in search as plain characters | Correctness |
| 5 | Make the interrupted-tool spec interrupt a tool | Specs |
| 6 | Spec the two untested compaction paths | Specs |
| 7 | Load the avoid list in one query | Efficiency |
| 8 | Split `conversation/runner.py` | Organization |
| 9 | Move the tool-backing services out of `conversation/service.py` | Organization |
| 10 | Delete dead code | Readability |
| 11 | Move `LimitReached` into `errors.py` | Organization |

**One ordering constraint:** do items 5 and 6 before item 8, so the failure
paths have specs before the runner's code moves.

---

## Privacy

### 1. Opt every model request out of OpenAI storage

**Problem:**
- Chat and the safety check set `openai_store=False` per agent.
- The Harness summarizer gets the model but no settings. When `store` is unset,
  the pinned adapter leaves it out of the request, and OpenAI then defaults to
  allowing response storage.
- Compaction sends older user history, so those requests allow OpenAI to store
  it. That contradicts `docs/privacy.md` and D-047. We haven't verified what
  OpenAI actually retained; the problem is what the request permits.

**Change:**
- In `src/capper/agent/agent.py`, `build_model`, set it once on the model so
  every agent using the model inherits it:

  ```python
  return OpenAIResponsesModel(
      model_name,
      provider=OpenAIProvider(openai_client=client),
      # Every request from this model, the summarizer's included, opts out of storage (D-047).
      settings=OpenAIResponsesModelSettings(openai_store=False),
  )
  ```

- Remove `openai_store=False` from `base_model_settings` and
  `safety_model_settings`; the model now carries it.
- Add a spec in `tests/capper/agent/test_agent.py` that checks the request
  itself:
  - send a compaction request through a model built by `build_model`, with
    the OpenAI client on a mock HTTP transport (`httpx.MockTransport`);
  - assert the captured request body has `"store": false`.

  This checks the behavior the fix guarantees, not just the configuration.

**Why:**
- The chat, summarizer and safety-check models all come from `build_model`
  (`app.py:94–95`), and Pydantic AI merges a model's default settings into
  every request it makes.
- Setting it once covers all three paths, and no future path can miss it.

### 2. Hide query values from logged errors

**Problem:**
- SQLAlchemy puts a failed statement's bound values in its error message.
- `logger.exception("saving turn %s failed", …)` (`runner.py:345`) would then
  log the assistant's text and the stored model messages.
- That breaks OBS-4 ("no message content in logs"), for database errors.

**Change:**
- In `src/capper/db.py`, `create_engine`:

  ```python
  engine = create_async_engine(database_url, hide_parameters=True)
  ```

- Add a spec in `tests/capper/test_db.py`: run a failing statement with a
  bound value such as `"private words"`, and assert the value isn't in
  `str(error)`.

**Why:**
- It's a focused fix for database errors, the path we confirmed, and it takes
  one argument.
- It isn't the only way content could reach the logs: provider and framework
  exceptions can carry response details. This narrow fix is enough for the MVP.
- Tracebacks stay, so failures remain debuggable.

---

## Correctness

### 3. One paging helper that validates cursors

**Problem:**
- `decode_cursor` (`paging.py:40`) checks only that the cursor is a list of
  the right length. Wrong field types reach the repositories, where
  `datetime.fromisoformat` raises a raw `TypeError` or `ValueError`:
  - `catalog/repository.py:58`: a model-supplied cursor fails the whole turn,
    because `ToolGuard` only turns `DomainError`s into tool results;
  - `conversation/repository.py:111`: an API client gets a 500.
- Separately, five list methods repeat the same paging code: fetch `size + 1`,
  slice, then encode the last row's key. Four are in `catalog/service.py`
  (110–149), and one is `ConversationService.history`.

**Change:** in `src/capper/paging.py`:

```python
def encode_cursor(key: Sequence[object]) -> str:
    """A row's sort key as an opaque string; datetimes travel as ISO 8601 text."""
    values = [v.isoformat() if isinstance(v, datetime) else v for v in key]
    return base64.urlsafe_b64encode(json.dumps(values).encode()).decode().rstrip("=")


def decode_cursor(cursor: str | None, fields: tuple[type, ...]) -> list[Any] | None:
    """The sort key a cursor carries, checked against the list's key types."""
    if cursor is None:
        return None
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        key = json.loads(base64.urlsafe_b64decode(padded.encode()))
        if not isinstance(key, list) or len(key) != len(fields):
            raise ValueError("wrong shape")
        return [_field(value, kind) for value, kind in zip(key, fields, strict=True)]
    except (TypeError, ValueError, UnicodeDecodeError) as error:
        raise InvalidRequest("cursor is not valid; start again without a cursor") from error


def _field(value: object, kind: type) -> object:
    if kind is datetime and isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:  # `UtcDateTime` refuses these when the query binds them
            raise ValueError("a cursor datetime needs a timezone")
        return parsed
    if type(value) is not kind:  # exact, so True isn't accepted as an int
        raise TypeError(f"expected {kind.__name__}")
    return value


def next_page[R](
    rows: list[R], size: int, key: Callable[[R], Sequence[object]]
) -> tuple[list[R], str | None]:
    """Rows fetched with `size + 1`: the page, and a cursor if more remain."""
    if len(rows) <= size:
        return rows, None
    return rows[:size], encode_cursor(key(rows[size - 1]))
```

Each list declares its key types and uses `next_page`. For example,
`CatalogService.search`:

```python
after = decode_cursor(cursor, (str, int))
async with self._sessions() as session:
    rows, total = await repository.search_products(session, user_id, query, size + 1, after)
rows, next_cursor = next_page(rows, size, lambda p: (p.name, p.id))
items = [ProductSummary(p.id, p.name, short_description(p.description), p.price) for p in rows]
return Page(items, total, next_cursor)
```

Key types for each list:

| List | Fields | Key |
|---|---|---|
| `search` | `(str, int)` | `(p.name, p.id)` |
| `promotions` | `(datetime, int)` | `(p.ends_at, p.id)` |
| `purchases` | `(str, int)` | `(purchase.purchased_at, purchase.id)`; legacy text |
| `popular` | `(int, int)` | `(count, product_id)` |
| `history` | `(datetime, str)` | `(m.created_at, m.id)` |

Then:
- delete `_next_cursor` from `catalog/service.py`;
- remove the `datetime.fromisoformat(...)` calls in `catalog/repository.py:58`
  and `conversation/repository.py:111`, which now receive a `datetime`.

Spec (`tests/capper/test_paging.py`): a cursor with a valid envelope but bad
fields raises `InvalidRequest`. Cases:
- wrong types: `encode_cursor([1, "x"])` for `(str, int)`;
- not a date: `["not a date", 1]` for `(datetime, int)`;
- a date without a timezone: `["2026-01-01T00:00:00", 1]` for
  `(datetime, int)`. `fromisoformat` accepts it, but `UtcDateTime` would reject
  it when the query binds it, turning it into a 500.

**Why:**
- Bad input gets the documented error at the boundary that parses it, so
  repositories receive values of the right type.
- One helper replaces five copies of the paging steps. Each list states its
  key once, so a reader sees how it pages.

### 4. Treat `%` and `_` in search as plain characters

**Problem:** `catalog/repository.py:23` builds `f"%{query}%"` from user text,
so `%` and `_` act as wildcards. For example, "100%" matches anything
containing "100".

**Change:** use SQLAlchemy's built-in escaping:

```python
if query and query.strip():
    term = query.strip().lower()
    conditions.append(
        or_(
            func.lower(Product.name).contains(term, autoescape=True),
            func.lower(Product.description).contains(term, autoescape=True),
        )
    )
```

Spec: a search for `"%"` returns no products.

**Why:** search should match what the user typed. The framework escapes it, so
there's no escaping code of our own.

---

## Specs that prove the core guarantees

### 5. Make the interrupted-tool spec interrupt a tool

**Problem:**
- `test_the_next_turn_works_after_an_interrupted_tool_call`
  (`tests/capper/conversation/test_api.py:190`) never interrupts a tool call.
  The tool finishes, the model then fails, and the stored history ends with a
  complete call and result.
- The spec only shows that the next turn succeeds, which it would anyway.
  `build-log.md`'s claim that this guarantee is "proven by a spec" is
  overstated.

**Change:** rewrite the spec so the stop lands *inside* a running tool.
- Requesting a stop from the scripted model step, as it returns the tool call,
  isn't enough: the run may be cancelled before the tool starts, which tests a
  different case.
- Use the injected clock instead, which needs no test switch. `get_promotions`
  reads the clock, so a test clock can request the turn's stop when that tool
  calls it.

Then assert:
1. the tool started (its audit row exists) and the turn is saved as
   `stopped`;
2. what the stored model messages hold for that call;
3. the next turn's request to the model carries a result for the call, the
   framework's `interrupted` result, and the turn succeeds.

After the spec runs:
- **If the stored messages don't hold the result that API-14 promises,** stop
  and ask Sam whether the code or API-14's wording changes. This is item 4 of
  the discussion list in `mvp-plan.md`.
- **Either way, correct `build-log.md`.** Its claim that this guarantee is
  "proven by a spec" should describe what the new spec actually shows.

**Why:** a guarantee is only proven by a spec that exercises it.

### 6. Spec the two untested compaction paths

**Problem:** compaction is specced for a foreground summary and a reload.
Two paths aren't:
- a summary prepared in the background (`background_start` 0.8) and swapped in
  on a later request;
- a turn that compacts and then fails, where `end_turn` saves the summary on
  the error path too.

**Change:** add two specs to `tests/capper/context/test_compaction.py`. Write
the background-summary spec first: it exercises a distinct path that normal long
conversations take.

1. **Background summary.** Cross 80% of the trigger in one turn, and the
   trigger in a later request.
   - Assert the summary row is saved, with the watermark just before the kept
     suffix.
   - Assert the next turn's first request starts with that summary.
2. **Compact, then fail.** A turn compacts, then the chat model raises.
   - Assert the turn is saved as `error` and the summary row exists.
   - Assert the next turn loads from that summary.

Keep the current behavior when no reliable cutoff is found: save no summary,
and reload the full history.

**Why:** compaction persistence depends on the Harness's output shape
(`find_compaction`). These are the two paths most likely to break it, and the
exact Harness pin only protects us if specs exercise it.

---

## Efficiency

### 7. Load the avoid list in one query

**Problem:** `MemoryService.snapshot` (`memory/service.py:86`) calls
`session.get(Product, …)` once per avoided product, on every turn's start: up
to 100 point reads.

**Change:** in `src/capper/memory/repository.py`, return names with the list:

```python
async def list_avoided(session: AsyncSession, user_id: int) -> list[tuple[int, str]]:
    """The avoid list with product names, oldest first."""
    rows = await session.execute(
        select(AvoidedProduct.product_id, Product.name)
        .join(Product, Product.id == AvoidedProduct.product_id)
        .where(AvoidedProduct.user_id == user_id)
        .order_by(AvoidedProduct.created_at, AvoidedProduct.product_id)
    )
    return [(product_id, name) for product_id, name in rows]
```

In `snapshot`, build `[AvoidedItem(pid, name) for pid, name in avoided]`, and
delete the loop and the `"product {id}"` fallback.

**Why:**
- The join replaces the loop, with less code.
- The fallback can't happen: `avoided_products.product_id` is a foreign key to
  `Products`, and SQLite enforces foreign keys here.

---

## Readability and organization

### 8. Split `conversation/runner.py`

**Problem:**
- At 453 lines, `runner.py` is the largest module, and `_execute` mixes four
  jobs: running the agent, turning stream events into client events, saving,
  and telemetry.
- It also hosts helpers that belong elsewhere: `opaque_user_key`,
  `account_view` and `estimated_cost`.
- The first-token timer is a mutable list in a closure (`first_token`).

**Change:**

1. **New `conversation/turn_stream.py`.** A `TurnStream` class owns what the
   client sees of a running turn:
   - the queue;
   - the `TranscriptParts`;
   - the time to first token, as a field set once (`first_token_ms: int | None`).

   Its `card` method is the `CapperDeps.emit_card` sink, and its `on_events`
   method is the agent's event handler (text deltas, plus the context-usage
   span event). `EventQueue` moves here too. This replaces the three closures
   in `_execute`.
2. **New `conversation/turn_telemetry.py`.** Plain functions take the span:
   - `record_safety`;
   - `record_compaction`;
   - `record_outcome`;
   - `estimated_cost`;
   - `clearing_ran`.

   This is a move only: the trace records exactly what it records today. Keep
   the `context.clearing` and `context.compaction` span events, which OBS-3
   requires.
3. **Placeholder constant.** Set `placeholder=CLEARED_PLACEHOLDER` explicitly
   in `build_clearing` (`context/compaction.py`), and import the constant from
   there. The trace's "cleared" check then can't silently drift from the
   Harness's default string.
4. **Move the helpers:**
   - `opaque_user_key` to `agent/agent.py`, beside `run_model_settings`, which
     uses its result;
   - `account_view` to `context/builder.py`, beside the `AccountView` it
     builds;
   - update the three spec imports of `opaque_user_key`.
5. **What stays in `runner.py`:**
   - the task lifecycle (`start`, `shutdown`, `_run`, `_fail`);
   - `_execute`, now assembling the turn and saving it;
   - `_run_agent` with `messages_after`;
   - the compaction lookup.

   Extract only where it makes the turn's flow easier to read. There's no line
   target: the aim is for `_execute` to read as the turn's sequence of steps.

**Why:**
- Each new module has one reason to change: streaming to the client, or what
  the trace records.
- `_execute` reads top to bottom as the turn's sequence.
- It stays simple: one small class and plain functions, with no new
  abstraction layers.

### 9. Move the tool-backing services out of `conversation/service.py`

**Problem:**
- At 446 lines, `conversation/service.py` holds three services.
- `HistorySearchService` (with its `fts_query`) and `ToolAuditLog` serve the
  agent's tools, not the conversation API.
- A reader looking for the conversation use cases has to skip past them, and a
  reader looking for history search has to find it inside the conversation
  service.

**Change:**
- Move `fts_query` and `HistorySearchService` to
  `conversation/history_search.py`.
- Move `ToolAuditLog` to `conversation/audit.py`.
- Update the imports in `app.py` and the specs.
- `service.py` keeps `ConversationService` and its data types.

**Why:**
- File names then say what's inside.
- `service.py` shrinks to about 370 lines and holds one service.
- It's a pure move with no behavior change.

### 10. Delete dead code

**Problem:** these are set or defined but never used, so a reader goes looking
for a use that doesn't exist:

| Code | Where |
|---|---|
| `CapperDeps.opaque_key`, `.clock`, `.flagged_policies` | `agent/deps.py:86, 87, 94`; set in `runner.py:308–316`, never read by a tool or capability |
| `StopRegistry.is_stopping` | `conversation/stop.py:26` |
| `TokenVerifier.from_file` | `auth/service.py:37` |

**Change:** delete them, their assignments in the runner, and any imports they
leave unused (`field` and `Clock` in `deps.py`, `Path` in `auth/service.py` if
unused).

**Why:**
- `CapperDeps` should list exactly what tools and capabilities use.
- The flagged policies already reach the model through the request context,
  and the opaque key through the run's settings.

### 11. Move `LimitReached` into `errors.py`

**Problem:**
- Every domain error lives in `errors.py` with its status code, except
  `LimitReached`.
- It's defined in `memory/service.py:19–21` with `status_code = 409`, so that
  service declares an HTTP status, against code standard 6.5.

**Change:**
- Move the class into `errors.py`, next to `TurnInProgress`.
- Import it in `memory/service.py` and `tests/capper/memory/test_service.py`.

**Why:** all errors and their status codes stay in one place, and services stay
free of HTTP.

---

## Considered and left out

Don't make these changes; each was weighed and rejected.

- **Logging only sanitized error categories:** item 2 covers the leak.
- **Removing requirement IDs from routine comments:** they stay, for the
  planned check of the code against the TDD.
- **Nits, or explanations rather than changes:**
  - a typed services dependency for the routers;
  - the shared `LIMIT_REACHED` dict;
  - the `assert` in `runner.py`;
  - renaming `capper/time.py`;
  - the `super(…, configured)` call in `TemplateSummarizer`;
  - the cost estimate pricing summarizer tokens at the chat model's rate.
- **Out of scope:**
  - Docker port binding;
  - the demo page's sign-out;
  - the eval's grading and exit code.

---

## Done when

- Every item above is applied, with its spec.
- The checks pass in the `dev` container:

  ```bash
  docker compose run --rm dev pytest
  docker compose run --rm dev ruff format --check
  docker compose run --rm dev ruff check
  docker compose run --rm dev pyright
  ```

- These rules held throughout:
  - no test switches or mock modes in production code; specs stub through
    dependency injection;
  - the code follows `code-standards.md`;
  - Sam manages git, so nothing is committed.

---

# Refactor as applied (from the build log, 2026-11-18)

The changes above, applied as written except:

1. **The storage spec injects the OpenAI client.** `build_model` now hands its client to
   `openai_model(model_name, client)`, which sets `openai_store=False` on the model. The
   spec builds that model on a mock transport and drives a real compaction. The pinned
   OpenAI SDK sends through `httpx2`, so the mock transport comes from `httpx2`. The spec
   lives with the compaction specs, whose helpers it uses.
2. **`running_app` takes a compaction model and a clock**, the same injection points as
   `create_app`, so specs can pass their own.
3. **A tool call that never returns is now audited.** `ToolGuard` wrote the audit row
   only after the tool returned, so a stopped, timed-out or failing call left none (code
   standard 3.5). It now writes the row as `error` (a status DATA-12 already has) and
   re-raises. The interrupted-tool spec asserts the row, and fails without the fix.
4. **The background start is removed** (D-096). The background-summary spec showed that
   no prepared summary was ever used. The summarizer now runs as its own capability with
   its token trigger; the `FallbackCompaction` wrapper, the setting and the shutdown
   `aclose()` went with it. Every compaction spec passes unchanged.

## Verification

- **After the refactor (2026-11-18)**, in the `dev` container: `pytest` (113 passed),
  `ruff format --check`, `ruff check` and `pyright` all pass. Each new privacy,
  correctness and audit spec was confirmed to fail with its fix removed.
