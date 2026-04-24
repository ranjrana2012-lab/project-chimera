.PHONY: help install-deps dev lint format test test-unit test-integration

help:
	@echo "Project Chimera - Make Targets"
	@echo ""
	@echo "Development:"
	@echo "  make install-deps    - Install python dev dependencies"
	@echo "  make dev             - Start all docker-compose services"
	@echo "  make lint            - Run ruff linter"
	@echo "  make format          - Run black formatter"
	@echo "  make test            - Run all pytest test suites"
	@echo "  make test-unit       - Run only unit tests"
	@echo "  make test-integration- Run only integration tests"
	@echo ""
	@echo "Observability:"
	@echo "  make silence-alerts  - Silence AlertManager alerts"

install-deps:
	pip install -r requirements-dev.txt

dev:
	docker compose -f docker-compose.mvp.yml up -d

lint:
	ruff check .

format:
	black .

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

silence-alerts:
	./scripts/silence-alerts.sh $(DURATION) $(COMMENT) $(MATCHERS)
