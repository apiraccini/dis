.PHONY: help lint test build start stop logs

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  help   Show this help"
	@echo "  lint   Lint backend + frontend"
	@echo "  test   Run all tests"
	@echo "  build  Build Docker images"
	@echo "  start  Start services (docker compose up -d)"
	@echo "  stop   Stop services (docker compose down)"
	@echo "  logs   Follow service logs"

lint:
	cd backend && uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/ && uv run ty check
	cd frontend && bun run lint

test:
	cd backend && uv run pytest
	cd frontend && bun run test

build:
	docker compose build

start:
	docker compose up -d

stop:
	docker compose down

logs:
	docker compose logs -f
