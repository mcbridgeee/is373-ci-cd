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
# Same restrictions compose.yaml gives prod, so a test pass means the image
# works the way it will actually run.
docker run -d --name "$NAME" \
  --read-only --cap-drop=ALL --security-opt=no-new-privileges:true \
  --pids-limit=128 --tmpfs=/tmp:rw,noexec,nosuid,nodev,size=64m,mode=1777 \
  -p "127.0.0.1:${E2E_PORT}:8000" "$IMAGE" >/dev/null

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

HEALTH="$(curl -fsS "$URL/health")"
echo "Healthy: $HEALTH"

# The running release must be the commit the image was built from.
EXPECTED_COMMIT="$(docker image inspect "$IMAGE" --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}')"
python3 -c 'import json,sys; c=json.loads(sys.argv[1])["commit"]; sys.exit(0 if c==sys.argv[2] else f"/health commit {c} != image label {sys.argv[2]}")' "$HEALTH" "$EXPECTED_COMMIT"

# Check the hardening from inside: unprivileged user, no installers, read-only
# code, no capabilities, and no way to gain privileges.
docker exec "$NAME" python -c '
import importlib.util, os
from pathlib import Path
assert (os.getuid(), os.getgid()) == (10001, 10001), "not running as appuser"
assert all(importlib.util.find_spec(m) is None for m in ("pip", "setuptools", "ensurepip")), "installer present"
assert not os.access("/app/app/main.py", os.W_OK), "app code is writable"
status = Path("/proc/self/status").read_text()
assert "NoNewPrivs:\t1" in status, "no-new-privileges not set"
assert "CapEff:\t0000000000000000" in status, "capabilities not dropped"
print("Container hardening checks passed")
'
E2E_BASE_URL="$URL" uv run --frozen pytest tests/e2e -q \
  --browser chromium \
  --tracing retain-on-failure \
  --screenshot only-on-failure \
  --output artifacts/playwright

# Record exactly which image passed, so CI can publish that image and nothing else.
mkdir -p .state
docker image inspect "$IMAGE" --format '{"image_id": "{{.Id}}", "commit": "'"$EXPECTED_COMMIT"'", "architecture": "{{.Architecture}}", "os": "{{.Os}}"}' > .state/tested-image.json
echo "Verified $(cat .state/tested-image.json)"
