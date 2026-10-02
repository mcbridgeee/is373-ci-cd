# Release image for the toothpaste quiz.
# Built once by `make build` (and later by CI), then tested and promoted
# without being rebuilt. Target platform is linux/amd64 (see docs/architecture.md).

# --- Stage 0: pinned base with current Debian security fixes ---
# The digest pins the exact base; Dependabot proposes updates to it.
FROM python:3.13.15-slim-trixie@sha256:7c61056e61ac89e852de05f3dc6fa51a6dd2181797bceed46aa725dd7cb2cd3b AS base
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# --- Stage 1: install only the runtime dependencies from the lockfile ---
FROM base AS dependencies
WORKDIR /app
RUN pip install --no-cache-dir uv==0.12.15
COPY pyproject.toml uv.lock ./
# --no-dev keeps pytest and Playwright out of the final image.
RUN uv sync --frozen --no-dev --no-install-project --python /usr/local/bin/python

# --- Stage 2: the small image that actually runs ---
FROM base AS runtime
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

# Nothing installs packages at runtime, so remove the installers (and the
# vulnerabilities that ship with them), then add an unprivileged user.
RUN python -m pip uninstall --yes pip setuptools \
    && python -c "import ensurepip, pathlib, shutil; shutil.rmtree(pathlib.Path(ensurepip.__file__).parent)" \
    && groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin appuser

# Code stays owned by root, so the app user cannot modify it.
COPY --from=dependencies /app/.venv /app/.venv
COPY app ./app

# Release identity, shown by /health and the page footer (QUIZ-30, QUIZ-31).
ARG BUILD_COMMIT=local
ARG BUILD_TIME=unknown
ENV BUILD_COMMIT=$BUILD_COMMIT \
    BUILD_TIME=$BUILD_TIME
LABEL org.opencontainers.image.source="https://github.com/mcbridgeee/is373-ci-cd" \
      org.opencontainers.image.revision="$BUILD_COMMIT" \
      org.opencontainers.image.created="$BUILD_TIME"

USER 10001:10001
# Port 8000 inside the container. Compose maps it to 8080 (dev) and 8090 (prod)
# on 127.0.0.1, and Traefik on the droplet routes to 8000 directly.
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=6 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
