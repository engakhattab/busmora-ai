# syntax=docker/dockerfile:1.7
#
# One Dockerfile, three targets (one per process role). Build from the repo root:
#   docker build -f deploy/Dockerfile --target ai-http  -t busmora-ai-http  .
#   docker build -f deploy/Dockerfile --target ai-agent -t busmora-ai-agent .
#   docker build -f deploy/Dockerfile --target ai-crawl -t busmora-ai-crawl .
#
# ai-http and ai-agent share a slim environment without browsers. Only ai-crawl
# installs the `crawl` extra and its browsers (docs/adr/0006).

ARG PYTHON_IMAGE=python:3.13.18-slim-trixie
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.13.8

FROM ${UV_IMAGE} AS uv

# ------------------------------------------------------------------ build stages
FROM ${PYTHON_IMAGE} AS build-base
COPY --from=uv /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /src

FROM build-base AS build-core
# Dependencies first (cached layer), then the project itself, non-editable.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=packages/busmora-ai-contracts/pyproject.toml,target=packages/busmora-ai-contracts/pyproject.toml \
    uv sync --locked --no-dev --no-install-workspace --no-install-project
COPY . /src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

FROM build-base AS build-crawl
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=packages/busmora-ai-contracts/pyproject.toml,target=packages/busmora-ai-contracts/pyproject.toml \
    uv sync --locked --no-dev --extra crawl --no-install-workspace --no-install-project
COPY . /src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --extra crawl --no-editable

# ------------------------------------------------------------------ runtime base
FROM ${PYTHON_IMAGE} AS runtime-base
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --home-dir /nonexistent app
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    BUSMORA_AI_LOG_FORMAT=json
WORKDIR /app

# ------------------------------------------------------------------ ai-http
FROM runtime-base AS ai-http
COPY --from=build-core /app/.venv /app/.venv
ENV BUSMORA_AI_SERVER__HOST=0.0.0.0 \
    BUSMORA_AI_SERVER__PORT=8100
USER app
EXPOSE 8100
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8100/health/live', timeout=3)"]
CMD ["busmora-ai-http"]

# ------------------------------------------------------------------ ai-agent
FROM runtime-base AS ai-agent
COPY --from=build-core /app/.venv /app/.venv
ENV BUSMORA_AI_HEALTH_SERVER__HOST=0.0.0.0 \
    BUSMORA_AI_HEALTH_SERVER__PORT=8101
USER app
EXPOSE 8101
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8101/health/live', timeout=3)"]
CMD ["busmora-ai-agent"]

# ------------------------------------------------------------------ ai-crawl
FROM runtime-base AS ai-crawl
COPY --from=build-crawl /app/.venv /app/.venv
# Browsers and their system libraries need root; keep them where the app user can read.
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright \
    HOME=/opt/crawl-home
RUN mkdir -p /opt/crawl-home \
    && scrapling install \
    && chmod -R a+rX /opt/ms-playwright /opt/crawl-home \
    && rm -rf /var/lib/apt/lists/*
ENV BUSMORA_AI_HEALTH_SERVER__HOST=0.0.0.0 \
    BUSMORA_AI_HEALTH_SERVER__PORT=8102
USER app
EXPOSE 8102
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8102/health/live', timeout=3)"]
CMD ["busmora-ai-crawl"]
