# Command interface for the toothpaste quiz (see CONTRIBUTING.md).
# Build and test targets are short shell recipes so you can read exactly what
# they do. Production lifecycle lives in scripts/runtime.py because it keeps state.

IMAGE    ?= is373-ci-cd:local
E2E_PORT ?= 18090
COMMIT   := $(shell git rev-parse HEAD 2>/dev/null || echo local)$(shell git status --porcelain 2>/dev/null | grep -q . && echo -dirty)
BUILT_AT := $(shell date -u +%Y-%m-%dT%H:%M:%SZ)

.PHONY: setup browsers test-unit test-integration build test-e2e dev up deploy verify-production rollback pause-updates resume-updates check-updates down status

## Install Python dependencies (including test tools) from uv.lock.
setup:
	uv sync --frozen

## Download the Chromium browser Playwright uses.
browsers:
	uv run --frozen playwright install chromium

## Pure Python tests of the quiz logic.
test-unit:
	uv run --frozen pytest tests/unit -q

## API tests run in-process with FastAPI's TestClient.
test-integration:
	uv run --frozen pytest tests/integration -q

## Build the release image once, stamped with the commit and UTC time. Does not publish.
build:
	docker build --platform linux/amd64 \
		--build-arg BUILD_COMMIT=$(COMMIT) \
		--build-arg BUILD_TIME=$(BUILT_AT) \
		-t $(IMAGE) .

## Browser tests against the built image in a throwaway container.
test-e2e:
	IMAGE=$(IMAGE) E2E_PORT=$(E2E_PORT) bash scripts/test-e2e.sh

## Start only dev on :8080 (no published image needed).
dev:
	docker compose up -d --build dev

## Production lifecycle (scripts/runtime.py). Each command honors a persisted
## rollback in .state/ and a local compose.override.yaml.
##   up                 dev + published prod + WUD (local demo)
##   deploy             published prod + WUD only; no build (the droplet)
##   verify-production  running image ID and /health commit match the selection
##   rollback           RELEASE=sha-<full commit> or sha256:<digest>; pauses WUD
##   resume-updates     back to the prod tag, then WUD resumes
export RELEASE
up deploy verify-production rollback pause-updates resume-updates check-updates status:
	python3 scripts/runtime.py $@

## Stop this project's services. Keeps volumes and anything not in compose.yaml.
down:
	docker compose down
