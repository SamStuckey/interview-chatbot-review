# Developer reference

See the [README](../README.md) for setup and [How to use Capper](how-to-use.md)
for demo usage, Jaeger, and check commands.

Run the commands below from the repository directory, after completing the
quick start and creating `.env`.

## Containers and data

| Service | Role |
|---|---|
| `init` | Creates development signing keys if needed, copies the supplied database if absent, runs migrations, seeds demo records, and publishes content. It exits after setup. |
| `capper` | Serves the app on port 8000 after `init` succeeds and `traces` starts. `GET /healthz` checks whether the database answers a query. |
| `traces` | Jaeger, with its UI on port 16686 and OTLP HTTP ingestion on port 4318 inside the Compose network. Trace storage is ephemeral in this configuration. |
| `dev` | Contains development and evaluation tools. Its optional Compose profile keeps it out of a normal `up`; invoke it explicitly with `docker compose run`. |

The `capper-data` volume holds the database and signing keys at `/app/data` by
default. The health check does not test model access or whether the provider can
answer a request.

The runtime image installs the app as a package; the dev image includes the
source, tests, and evals. Neither mounts your working tree, so rebuild after local
changes. In particular,
`docker compose up --build -d` does not build the optional `dev` image; use
`docker compose build dev` before checking changed code.

Setup can be rerun without replacing the existing database or duplicating
unchanged seed records. It does add missing seed records, so deleting a seeded
guidance note or avoided product in the demo can be undone by the next setup
run. See [scripts/bootstrap.py](../scripts/bootstrap.py) and
[scripts/seed.py](../scripts/seed.py) for the exact behavior.

For content-only edits, `docker compose run --rm --build init` publishes changed
documents and deactivates documents removed from the manifest, without restarting
the running app. This command also reruns the other setup steps above. Each turn
reads a content snapshot, so the next turn uses the updated content.

## Database console

With the app running, open Python's SQLite console:

```bash
docker compose exec capper python -m sqlite3 /app/data/capper.db
```

If `make` is installed, `make sql-console` runs the same command. Exit with `.quit`
or Ctrl+D.

## Evals and the API contract

Evals require the initialized database and signing keys from setup, plus valid
model credentials in `.env`. They run their own app in-process and use temporary
database copies; the running `capper` service does not handle eval requests.
Existing demo history is included in the copy and can affect results. Trace
export is disabled for these eval runs.

- [tool_call_eval.py](../evals/tool_call_eval.py) checks eight cases: five safety
  prompts that should load particular policies and three ordinary requests that
  should not load a safety policy. It checks successful policy reads, not the
  quality of the final answer.
- [answer_quality_eval.py](../evals/answer_quality_eval.py) judges three replies,
  including their cards: referral steps, disclosure of a partial product list,
  and avoiding allergy-safety promises. It prints pass/fail results with reasons.
  Its judge model is set by `JUDGE_MODEL` in that module, independently of the
  app's chat and compaction model settings.

Both call OpenAI and incur API costs. Both exit nonzero if a case fails or cannot
be evaluated. These are small demo checks; the judge has not been calibrated
against a human-labeled benchmark. Run commands are in
[How to use Capper](how-to-use.md#tests-and-evals).

[tests/capper/openapi.json](../tests/capper/openapi.json) is a snapshot of the API
contract. A test fails when it differs from the app's generated schema. The
export creates the app, so it needs the configured signing keys from setup,
but it does not make a model request. After an intentional API change:

```bash
docker compose build dev
docker compose run --rm dev python -m scripts.export_openapi > tests/capper/openapi.json
docker compose build dev
docker compose run --rm dev pytest tests/capper/test_app.py
```

The second build includes the regenerated snapshot in the dev image. Review the
JSON diff before committing the contract change.

## Layout

| Path | What lives there |
|---|---|
| `src/capper/app.py` | App creation and dependency wiring |
| `src/capper/config.py` | Environment settings, defaults, and validation |
| `src/capper/db.py` | Database engine, sessions, and shared database types |
| `src/capper/telemetry.py` | Logging and trace-export setup |
| `src/capper/agent/` | The agent, its dependencies, and tools |
| `src/capper/context/` | Context assembly, tool-result clearing, and summary handling |
| `src/capper/conversation/` | Conversation routes, stored turns, history search, streaming, cancellation, tool audits, and turn telemetry |
| `src/capper/accounts/` | Users, schools, referral codes, and account queries |
| `src/capper/catalog/` | Products, promotions, purchases, and catalog queries |
| `src/capper/memory/` | Saved guidance notes and avoided products |
| `src/capper/auth/` | Bearer-token verification and demo token signing |
| `src/capper/catalog/product_images/` | The product images (SVG), served at `/images/products/…` |
| `src/capper/demo/` | The demo page and its sign-in routes |
| `src/capper/health/` | `GET /healthz` |
| `src/content_bundle/` | The content table and its read/publish functions, shared by service and ingestion |
| `src/ingestion/` | Reads the content manifest and publishes the documents |
| `content/` | The authored content (`manifest.toml` lists what's published) |
| `alembic/` | Schema migrations and migration environment |
| `Dockerfile`, `compose.yaml` | The `runtime` and `dev` images; the `init`, `capper`, `traces` and `dev` services |
| `scripts/` | The `init` service's bootstrap, the demo seed data, and the OpenAPI export |
| `tests/` | Tests, organized to follow the source layout |
| `evals/` | Real-model evals |
| `docs/` | The design documents and diagrams, usage guides, decisions, and project history |

## Dependencies

The dependency declarations live in [pyproject.toml](../pyproject.toml); exact
resolved versions live in [uv.lock](../uv.lock). Docker builds use
`uv sync --locked`, so an out-of-date lockfile fails the build.

Runtime packages are installed in both the runtime and dev images:

| Package | Why |
|---|---|
| `fastapi` | HTTP routes, request validation, API schema, and streaming responses |
| `uvicorn` | The ASGI server |
| `pydantic-ai-slim[openai]` | The agent framework and its OpenAI Responses model |
| `pydantic-ai-harness` | Tool-result clearing, compaction and context-usage reporting; pinned exactly |
| `pydantic-settings` | Settings from the environment (Compose passes `.env` in) |
| `sqlalchemy[asyncio]` | The ORM and async data access |
| `aiosqlite` | The async SQLite driver |
| `alembic` | Schema migrations |
| `pyjwt[crypto]` | RS256 bearer-token verification and demo token signing; its cryptography extra also supplies signing-key generation |
| `opentelemetry-sdk` | Trace creation, resources, and span processing |
| `opentelemetry-exporter-otlp-proto-http` | Exporting traces to Jaeger over OTLP HTTP |

The dev image also installs both dependency groups:

| Group | Package | Purpose |
|---|---|---|
| `dev` | `pytest`, `pytest-asyncio` | Tests and async test support |
| `dev` | `httpx` | HTTP clients for tests and in-process eval requests |
| `dev` | `httpx2` | Mock transports for the OpenAI client in specs (the SDK's own HTTP library) |
| `dev` | `ruff` | Formatting and linting |
| `dev` | `pyright` | Strict type checking |
| `dev` | `pip-audit` | Dependency vulnerability checks |
| `evals` | `pydantic-evals` | Evaluation datasets, grading, and reports |

Build tooling: the Dockerfile pins Python and uv; the project requires Python
3.14 or newer. uv installs the environment, and `hatchling` is the Python package
build backend. Pyright's Python wrapper installs Node during the dev-image build.
Jaeger runs in its own pinned container image.
