# Image for a project built from this template: dashboard + API (and, optionally, MCP).
# Build:  docker build -t my-agents .
# Run:    docker run -p 127.0.0.1:8787:8787 -e CATALOG_TOKEN=change-me -v agents-data:/data my-agents
# Or use docker compose (see docker-compose.yml and "Run and deploy" in the README).

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1

WORKDIR /srv

# Dependencies first, so code changes do not reinstall them.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-install-project --no-dev

COPY . .
RUN uv sync --locked --no-dev \
    && useradd --create-home --uid 10001 app \
    && mkdir -p /data && chown app:app /data

# State lives in the /data volume: catalog choices and settings edited in the dashboard.
ENV PATH="/srv/.venv/bin:$PATH" \
    HOST=0.0.0.0 \
    PORT=8787 \
    CATALOG_DB=/data/catalog.sqlite3 \
    CATALOG_ENV_FILE=/data/.env

USER app
VOLUME ["/data"]
EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8787\")}/health', timeout=4)"

# Refuses to start without CATALOG_TOKEN, because it listens on all interfaces.
CMD ["python", "-m", "app", "serve"]
