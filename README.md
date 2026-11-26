# Capper

Capper is a proof-of-concept assistant for the Carton Caps app. It helps users
discover products, find Bonus Caps offers, and get referral support using their
purchase history and saved preferences. It runs locally in Docker with a browser
demo and trace viewer.

The engineering focus is managing context across a continuing conversation:
limiting history, clearing older tool results, saving summaries, and retrieving
past messages. See [Features](docs/features.md) for the implementation and
[Known limitations](docs/known-limitations.md) for its gaps.

## Requested artifacts

Where each part of the [challenge brief](docs/challenge-criteria.md) is
answered.

**Deliverable 1: conversational AI design and LLM strategy**

| The brief asks for | Where |
|---|---|
| The API contract for creating and maintaining conversations | [API contract](docs/api-contract.md), with the generated [OpenAPI snapshot](tests/capper/openapi.json) |
| Diagrams for onboarding engineers | [System overview](docs/diagrams/system-overview.md), [the agent loop](docs/diagrams/agent-loop.md), [content and knowledge updates](docs/diagrams/content-updates.md) |
| Integration into the mobile app | [Mobile integration](docs/mobile-integration.md) |
| Privacy considerations | [Privacy](docs/privacy.md) |
| Conversation design principles, trade-offs, reasoning, priorities and evolution | [Point of view](docs/point-of-view.md), with every decision in the [decision log](docs/decision-log.md) |
| Staying aligned with the assistant's purpose | [Point of view](docs/point-of-view.md#conversation-design-principles) and [Features](docs/features.md#policy-handling-and-scope) |
| Handling data and knowledge-base updates | [Content and knowledge updates](docs/diagrams/content-updates.md) |

**Deliverable 2: prototype conversational AI service**

| The brief asks for | Where |
|---|---|
| A working API with multi-turn conversations | [src/capper/conversation/](src/capper/conversation/); run it with the [quick start](#quick-start) |
| An LLM integration | [src/capper/agent/](src/capper/agent/) (Pydantic AI on OpenAI) |
| Preprocessing, prompt engineering and context management | [src/capper/context/](src/capper/context/), [content/](content/) and [src/ingestion/](src/ingestion/) |
| Unit and integration tests | [tests/](tests/), plus real-model [evals](evals/); see [How to use Capper](docs/how-to-use.md#tests-and-evals) |

The [checkpoints](docs/checkpoints/) are the project's history: design
reviews, the build log and cleanup passes, kept as they were written. They are
not updated as the code changes and may be out of date. The code and the
documents above are current.

## Quick start

You need Docker with Compose v2 and an OpenAI API key. The default models are
`gpt-6.1-terra` for chat and `gpt-6-luna` for summarization. Ports 8000 and 16686
must be free. Python runs inside Docker.

1. Clone the repository, or open your existing checkout:

   ```bash
   git clone git@github.com:livefront-code-challenges/ai-solutions-challenge-20261112-sam-stuckey.git
   cd ai-solutions-challenge-20261112-sam-stuckey
   ```

2. Copy the configuration template:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set `OPENAI_API_KEY` and `CAPPER_CACHE_KEY_SECRET`.
   Use a long random string for the secret; `openssl rand -hex 32` generates one.
   `.env` is excluded from version control.

3. Build and start the app:

   ```bash
   docker compose up --build -d
   docker compose ps
   ```

   The first build takes a few minutes. Setup creates signing keys, prepares the
   database, and publishes the bundled content. Wait for `capper` to show
   `(healthy)`, then open [the demo](http://localhost:8000/).

Once the app is running, follow the [walk-throughs](docs/walk-throughs.md) to
try a recommendation, inspect its Jaeger trace, and check saved data in SQL.
[How to use Capper](docs/how-to-use.md) covers the demo controls, running Jaeger,
everyday commands, troubleshooting, tests, and evals.

## Configuration

Set overrides in `.env`, then run `docker compose up -d` to apply them. Common
settings include `CAPPER_CHAT_MODEL`, `CAPPER_COMPACTION_MODEL`, and
`CAPPER_HISTORY_BUDGET_TOKENS`. [config.py](src/capper/config.py) defines all
settings and defaults; [.env.example](.env.example) provides a starting point.

## Further reading

Requested artifacts:

- [API contract](docs/api-contract.md): endpoints, stream events, send rules, and turn outcomes.
- [Diagrams](docs/diagrams/): the [system overview](docs/diagrams/system-overview.md), [the agent loop](docs/diagrams/agent-loop.md), and [content and knowledge updates](docs/diagrams/content-updates.md).
- [Mobile integration](docs/mobile-integration.md): how the Carton Caps app would use the API.
- [Privacy](docs/privacy.md): what is stored, sent, and kept out of logs and traces.
- [Point of view](docs/point-of-view.md): priorities, trade-offs, and how the design would evolve.

Using and understanding Capper:

- [Walk-throughs](docs/walk-throughs.md): guided examples from chat to traces and SQL.
- [How to use Capper](docs/how-to-use.md): demo usage, Jaeger, commands, tests, and evals.
- [Features](docs/features.md): implemented behavior and its source requirements.
- [Known limitations](docs/known-limitations.md): scope choices, gaps, and future work.
- [Developer reference](docs/development.md): project layout, dependencies, database access, and API snapshot updates.
- [Code standards](docs/code-standards.md): project conventions.

Background and history:

- [Challenge brief](docs/challenge-criteria.md): the assignment.
- [Decision log](docs/decision-log.md): every engineering decision and its reasoning, as made.
- [Checkpoints](docs/checkpoints/): design, build, and review history. Not kept current; may be out of date.
- [Conversation log](docs/conversation-log.md): the working session record.
