# How to use Capper

Follow the [quick start](../README.md#quick-start) first. This guide covers the
demo, Jaeger, everyday commands, and checks. For guided examples with SQL queries,
see [Walk-throughs](walk-throughs.md).

## Try it

Choose a user to start chatting. Demo sign-in lets you select an account without
credentials; authenticated requests then use a signed bearer token.

| User | What to try |
|---|---|
| Tracy Mendez | An established user with purchases. Ask “What Bonus Caps offers are available?” or “How do I refer a friend?” |
| Tyler Roberts | Has a saved peanut-allergy note and an avoided product. Ask for snack suggestions; the catalog has no allergen data, so Capper cannot confirm allergy safety. |
| Nora Newcomer | Starts without purchases or saved preferences. Say “Remember that I prefer quick weeknight meals,” then ask for suggestions. |

Replies stream into the page and can include product and Bonus Caps cards. The
send button becomes a stop button during a reply. Use **Switch user** to try
another account; each user's conversation and saved preferences persist.

To inspect a turn, open [Jaeger](http://localhost:16686/), select the **Search**
tab, choose service **capper**, and click **Find Traces**. Open a result to see
its individual model and tool operations. Traces show timings and token counts
with message-content capture disabled. The interactive
[API docs](http://localhost:8000/docs) describe the endpoints and request schemas.

### Limitations

Current behavior is rudimentary. For example, catalog search matches text in
product names and descriptions; it has no semantic search or synonym expansion.
And if you want the model to remember something about you, you have to
explicitly say "remember X". This was a decision made to avoid implementing a
confirmation step in this MVP. These and other known limitations, and their
rationale, are discussed in the [Features](features.md) and
[Known limitations](known-limitations.md) docs.


## Jaeger: run and inspect traces

Jaeger is already running if you completed the quick start: the same
`docker compose up --build -d` command starts the app and the trace viewer.
Open [Jaeger](http://localhost:16686/) in another browser tab.

### Find the turn

1. Send a message in the demo and wait for the reply to finish.
2. In Jaeger, select the **Search** tab.
3. Select **capper** in the **Service** dropdown. Leave **Operation** unfiltered
   and choose a lookback that covers your message, such as the last hour.
4. Click **Find Traces**. If `capper` or the trace is missing, wait a few seconds
   for export and search again.
5. Find the result with the timestamp matching your message and click its title,
   such as **capper: capper.turn 7c913c1**. The checkbox is for comparing traces.

Each result summarizes a turn; it does not list the tools it contains. The
**Spans** count includes the turn, agent, model requests, and tool calls.

### Read the timeline

1. Expand the arrows beside **capper.turn** and **invoke_agent capper** if needed.
2. Look down the operation names on the left. `chat …` rows are model requests;
   `execute_tool …` rows name the tools, such as `search_products` or
   `show_products`. Click a row to open its span details and timing.
3. Click the top-level **capper.turn** row and expand **Tags**. Useful fields
   include `capper.status`, `capper.tool_calls`, `capper.input_tokens`,
   `capper.output_tokens`, and `capper.time_to_first_token_ms`.
4. Copy **capper.turn_id** to correlate the turn with database records. Jaeger's
   TraceID, SpanID, and the short ID on the search result are different IDs.

The **Process** section contains service metadata. Message text, search queries,
tool arguments, and tool results are intentionally omitted from traces; they
will not appear by expanding more sections. The tool audit also redacts free-text
arguments. See [the recommendation walk-through](walk-throughs.md#1-recommend-products-then-save-a-preference)
for a concrete example of inspecting tool calls, then reading a saved preference
in SQL.

### If traces are missing

Check service status and logs:

```bash
docker compose ps
docker compose logs -f traces
```

If the trace viewer has stopped, `docker compose up -d traces` starts it again.
Starting Jaeger alone does not create traces; send a new message in the app.

Also check the app logs (`docker compose logs -f capper`) and any
`CAPPER_OTLP_ENDPOINT` override. The default endpoint is `http://traces:4318`
inside the Compose network; the browser UI is on port 16686. Jaeger's trace
storage is ephemeral in this configuration, so use the database for saved turns
and tool audits.

For a step-by-step example connecting a chat reply, trace, and SQL records, see
[Walk-throughs](walk-throughs.md).

## Everyday commands

Run these from the repository directory:

| Task | Command |
|---|---|
| Start, or rebuild after code changes | `docker compose up --build -d` |
| Check readiness | `docker compose ps` |
| Follow app logs | `docker compose logs -f capper` |
| Stop and keep saved data | `docker compose down` |
| Publish content edits without restarting the app | `docker compose run --rm --build init` |
| Delete saved data and start fresh | `docker compose down -v`, then `docker compose up --build -d` |

The database and signing keys live in the `capper-data` Docker volume. Content,
images, and the demo page ship with the image; model requests go to OpenAI.
Published content changes take effect on the next turn.

### Troubleshooting

| Problem | What to check |
|---|---|
| Missing `.env` | Copy `.env.example` and fill in both required values. |
| Port already allocated | Free port 8000 or 16686, or change its host mapping in `compose.yaml`, such as `"8080:8000"`. |
| App never becomes healthy | Read `docker compose logs init`, then `docker compose logs capper`. |
| Replies fail | Check the app logs, your OpenAI key, and access to the configured models. |

## Tests and evals

Build the development image before running checks, and rebuild it after local
changes so the checks use the current code:

```bash
docker compose build dev
docker compose run --rm dev pytest
docker compose run --rm dev ruff format --check
docker compose run --rm dev ruff check
docker compose run --rm dev pyright
docker compose run --rm dev pip-audit
```

Tests use scripted models and make no real model calls. Evals call OpenAI and
incur API costs. Start the app once to initialize its data, then run:

```bash
docker compose run --rm dev python -m evals.tool_call_eval
docker compose run --rm dev python -m evals.answer_quality_eval
```

Evals use temporary database copies and exit nonzero on failure. They cover
policy selection and three judged replies. See the
[developer reference](development.md) for their scope and limitations.

