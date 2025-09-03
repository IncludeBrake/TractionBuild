# ==============================================================================
# tractionbuild Master Makefile
# ==============================================================================
# Provides a unified command interface for the entire project.

# Default shell
SHELL := /bin/bash

# --- Configuration ---
PYTHON_VERSION := 3.12
VENV_DIR := .venv
DOCKER_COMPOSE_FILE := docker-compose.yml
IMAGE_NAME := tractionbuild-app

.PHONY: help install test run up down clean scan docs

help:
	@echo "🚀 tractionbuild Project Commands:"
	@echo "--------------------------------------------------"
	@echo "  install      - Install all Python and Node.js dependencies."
	@echo "  test         - Run all Python unit and integration tests."
	@echo "  test-e2e     - Run the end-to-end API tests."
	@echo "  test-node    - Run Node.js tests and audit for vulnerabilities."
	@echo "  run          - Start the FastAPI server in development mode."
	@echo "  up           - Start all services with Docker Compose (detached)."
	@echo "  down         - Stop all services started with Docker Compose."
	@echo "  logs         - Tail the logs for all running Docker services."
	@echo "  clean        - Remove build artifacts, caches, and temp files."
	@echo "  scan         - Scan the Docker image for vulnerabilities with Trivy."
	@echo "  docs         - (Placeholder) Build project documentation."
	@echo "--------------------------------------------------"

# --- Installation & Dependencies ---
install:
	@echo "🐍 Installing Python dependencies with Poetry..."
	@poetry install
	@echo "📦 Installing Node.js dependencies..."
	@if [ -f web/package.json ]; then \
		(cd web && npm ci); \
	else \
		(npm ci); \
	fi
	@echo "✅ Dependencies installed."

# --- Testing ---
test:
	@echo "🧪 Running Python tests with pytest..."
	@poetry run pytest -q

test-e2e:
	@echo "🔬 Running End-to-End API tests..."
	@poetry run python tests/test_e2e.py

test-node:
	@echo "🧪 Running Node.js tests and audit..."
	@if [ -f web/package.json ]; then \
		(cd web && npm test && npm audit --audit-level=high); \
	else \
		(npm test && npm audit --audit-level=high); \
	fi


# --- Local Development ---
run:
	@echo "🔥 Starting Consolidated FastAPI server with Uvicorn..."
	@python -m uvicorn tractionbuild.api.app:app --reload --host 0.0.0.0 --port 8000 --app-dir src

# --- Docker & Deployment ---
up:
	@echo "🐳 Starting all services with Docker Compose..."
	@docker compose -f $(DOCKER_COMPOSE_FILE) up --build -d

down:
	@echo "🛑 Stopping all Docker Compose services..."
	@docker compose -f $(DOCKER_COMPOSE_FILE) down

logs:
	@echo "📋 Tailing logs for all services..."
	@docker compose -f $(DOCKER_COMPOSE_FILE) logs -f

# --- Security & Maintenance ---
scan:
	@echo "🛡️  Scanning Docker image for vulnerabilities..."
	@docker build -t $(IMAGE_NAME):latest .
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image $(IMAGE_NAME):latest

clean:
	@echo "🧹 Cleaning up project..."
	@rm -rf `find . -name __pycache__`
	@rm -f `find . -type f -name '*.py[co]'`
	@rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info
	@echo "✅ Cleanup complete."

# --- Documentation ---
docs:
	@echo "📚 Building documentation... (placeholder)"
	# Add your documentation generation command here, e.g., using Sphinx or MkDocs
