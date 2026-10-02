# Command interface for the toothpaste quiz (see CONTRIBUTING.md).
# Every target is a short, readable shell recipe on purpose, so you can see
# exactly what each command does.

IMAGE    ?= is373-ci-cd:local
E2E_PORT ?= 18090
COMMIT   := $(shell git rev-parse --short HEAD 2>/dev/null || echo local)
BUILT_AT := $(shell date -u +%Y-%m-%dT%H:%M:%SZ)

.PHONY: setup browsers test-unit test-integration build test-e2e

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
