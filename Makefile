.PHONY: help install dev-install test lint format clean docker-build docker-run docker-compose

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	pip install -r requirements.txt

dev-install: ## Install development dependencies
	pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install

test: ## Run all tests
	python test_architecture.py
	python test_comprehensive.py
	pytest tests/ -v

format: ## Format code
	ruff format app/ tests/
	black app/ tests/
	isort app/ tests/ --profile black

lint: ## Run linting
	ruff check app/ tests/
	./run_mypy.sh

lint-fix: ## Run linting with auto-fix
	ruff check --fix app/ tests/
	./run_mypy.sh

mypy: ## Run mypy type checking
	./run_mypy.sh

mypy-config: ## Run mypy with config file (may have issues with missing imports)
	mypy .

docker-compose: ## Run with docker-compose
	docker-compose up --build

run-dev: ## Run development server
	export PYTHONPATH=$$PWD && uvicorn app.presentation.api.main:app --reload --host 0.0.0.0 --port 8000

clean: ## Clean cache files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
