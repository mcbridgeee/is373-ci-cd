#!/usr/bin/env bash
# Run the browser tests against the already-built image, in its own
# throwaway container. The container is removed even if a test fails.
#
# Usage: scripts/test-e2e.sh  (normally via `make test-e2e`)
#   IMAGE     image to test        (default: is373-ci-cd:local)
#   E2E_PORT  host port to expose  (default: 18090)
set -euo pipefail

IMAGE="${IMAGE:-is373-ci-cd:local}"
E2E_PORT="${E2E_PORT:-18090}"
NAME="is373-ci-cd-e2e-$$"
URL="http://127.0.0.1:${E2E_PORT}"

cleanup() {
  docker rm -f "$NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "Image $IMAGE not found. Run 'make build' first." >&2
  exit 1
fi

echo "Starting $IMAGE as $NAME on $URL"
docker run -d --name "$NAME" -p "127.0.0.1:${E2E_PORT}:8000" "$IMAGE" >/dev/null

# Wait up to ~30s for the container to answer /health.
for _ in $(seq 1 60); do
  if curl -fsS "$URL/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done
if ! curl -fsS "$URL/health" >/dev/null 2>&1; then
  echo "Container never became healthy. Its logs:" >&2
  docker logs "$NAME" >&2 || true
  exit 1
fi

echo "Healthy: $(curl -fsS "$URL/health")"
E2E_BASE_URL="$URL" uv run --frozen pytest tests/e2e -q \
  --browser chromium \
  --tracing retain-on-failure \
  --screenshot only-on-failure \
  --output artifacts/playwright
