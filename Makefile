.PHONY: help install-deps dev profile student-up student-down dgx-config dgx-up dgx-down lint format test test-unit test-integration

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
PYTEST ?= $(PYTHON) -m pytest

help:
	@echo "Project Chimera - Make Targets"
	@echo ""
	@echo "Development:"
	@echo "  make install-deps    - Install python dev dependencies"
	@echo "  make dev             - Start all docker-compose services"
	@echo "  make profile         - Detect recommended runtime profile"
	@echo "  make student-up      - Start lightweight student dashboard"
	@echo "  make student-down    - Stop lightweight student dashboard"
	@echo "  make dgx-config      - Validate DGX Spark compose config"
	@echo "  make dgx-up          - Start MVP stack with DGX Spark override"
	@echo "  make dgx-down        - Stop MVP stack with DGX Spark override"
	@echo "  make lint            - Run ruff linter"
	@echo "  make format          - Run black formatter"
	@echo "  make test            - Run all pytest test suites"
	@echo "  make test-unit       - Run only unit tests"
	@echo "  make test-integration- Run only integration tests"
	@echo ""
	@echo "Observability:"
	@echo "  make silence-alerts  - Silence AlertManager alerts"

install-deps:
	$(PIP) install -r requirements-dev.txt

dev:
	docker compose -f docker-compose.mvp.yml up -d

profile:
	$(PYTHON) scripts/detect_runtime_profile.py

student-up:
	docker compose -f docker-compose.student.yml up -d --build

student-down:
	docker compose -f docker-compose.student.yml down

dgx-config:
	docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml config --services

dgx-up:
	docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d --build

dgx-down:
	docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml down

lint:
	ruff check .

format:
	black .

test:
	$(PYTEST) tests/ -v

test-unit:
	$(PYTEST) tests/unit/ -v

test-integration:
	$(PYTEST) tests/integration/ -v

silence-alerts:
	./scripts/silence-alerts.sh $(DURATION) $(COMMENT) $(MATCHERS)
