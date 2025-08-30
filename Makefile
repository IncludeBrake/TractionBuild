.PHONY: up down test fmt

up:
	docker compose up -d --build

down:
	docker compose down

test:
	python -m pytest tests/ -v

fmt:
	black src/ tests/
	isort src/ tests/
