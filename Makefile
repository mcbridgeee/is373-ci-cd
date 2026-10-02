# Command interface for the toothpaste quiz (see CONTRIBUTING.md).
# Every target is a short, readable shell recipe on purpose, so you can see
# exactly what each command does.

IMAGE    ?= is373-ci-cd:local
E2E_PORT ?= 18090
COMMIT   := $(shell git rev-parse HEAD 2>/dev/null || echo local)$(shell git status --porcelain 2>/dev/null | grep -q . && echo -dirty)
BUILT_AT := $(shell date -u +%Y-%m-%dT%H:%M:%SZ)

.PHONY: setup browsers test-unit test-integration build test-e2e scan dev up down status

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

## Scan the built image with the pinned Trivy; fails on fixable HIGH/CRITICAL.
scan:
	sh scripts/install-trivy.sh
	python3 scripts/scan-image.py $(IMAGE) artifacts/security

## Start only dev on :8080 (no published image needed).
dev:
	docker compose up -d --build dev

## Start dev, prod (published image), and WUD.
up:
	docker compose up -d --build

## Stop this project's services. Keeps volumes and anything not in compose.yaml.
down:
	docker compose down

## Show the services and what release each one reports.
status:
	@docker compose ps
	@echo "dev  /health: $$(curl -fsS http://127.0.0.1:8080/health 2>/dev/null || echo 'not running')"
	@echo "prod /health: $$(curl -fsS http://127.0.0.1:8090/health 2>/dev/null || echo 'not running')"
