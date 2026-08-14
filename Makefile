.PHONY: install dev test lint docker-up docker-down

install:
	pip install -e ".[dev]"

dev:
	uvicorn backend.main:app --reload --port 8000

test:
	pytest -v

lint:
	ruff check backend/ tests/
	ruff format --check backend/ tests/

format:
	ruff format backend/ tests/
	ruff check --fix backend/ tests/

docker-up:
	cp -n .env.example .env 2>/dev/null || true
	docker compose up --build

docker-down:
	docker compose down -v
