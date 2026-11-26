# Capper images, on the official Python slim image.
#   runtime: the service, and the init service's bootstrap. No dev or eval packages.
#   dev:     specs, checks and evals (`docker compose run --rm dev ...`).

FROM ghcr.io/astral-sh/uv:0.11.16 AS uv

FROM python:3.14.4-slim-bookworm AS base
COPY --from=uv /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR /app
# One non-root user for every image; it owns the data volume's mount point, so a fresh
# named volume starts out writable.
RUN useradd --uid 10001 --create-home capper && mkdir -p /app/data && chown capper /app/data

FROM base AS build
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-default-groups --no-install-project
COPY src ./src
RUN uv sync --locked --no-default-groups --no-editable

FROM base AS runtime
ARG GIT_SHA=""
COPY --from=build /app/.venv /app/.venv
COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts ./scripts
COPY content ./content
COPY ["supporting-files/Carton Caps Data.sqlite", "./supporting-files/"]
ENV CAPPER_GIT_SHA=${GIT_SHA}
USER capper
EXPOSE 8000
CMD ["python", "-m", "capper"]

FROM base AS dev
# pyright runs on Node, which its PyPI wrapper installs; that Node needs libatomic.
RUN apt-get update && apt-get install -y --no-install-recommends libatomic1 \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --all-groups --no-install-project
COPY . .
RUN uv sync --locked --all-groups && chown -R capper /app
USER capper
# Fetch pyright's Node at build time, so checks don't download anything when they run.
RUN pyright --version
CMD ["pytest"]
