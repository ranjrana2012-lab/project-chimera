# Makefile for Project Chimera

.PHONY: help dev test lint format build-all deploy \
        install-deps verify check-env clean \
        run-dev backup restore \
        bootstrap bootstrap-status bootstrap-destroy

# Default target
help:
	@echo "Project Chimera - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev           - Start local development environment"
	@echo "  make test          - Run all tests"
	@echo "  make lint          - Run linter"
	@echo "  make format        - Format code"
	@echo ""
	@echo "Building:"
	@echo "  make build-all     - Build all Docker images"
	@echo "  make build-service  SERVICE=name - Build specific service"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy        ENV=dev - Deploy to environment"
	@echo "  make backup        - Create backup"
	@echo "  make restore       BACKUP=path - Restore from backup"
	@echo ""
	@echo "Utilities:"
	@echo "  make install-deps   - Install dependencies"
	@echo "  make verify        - Verify environment"
	@echo "  make check-env      - Check environment setup"
	@echo "  make clean         - Clean build artifacts"

# Development
dev:
	docker-compose -f docker-compose.local.yml up -d
	@echo "Development environment started"
	@echo "Access Grafana: http://localhost:3000"
	@echo "Access Prometheus: http://localhost:9090"

# Testing
test:
	pytest tests/ -v --cov=services --cov-report=html
	@echo "Test coverage report: htmlcov/index.html"

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-load:
	pytest tests/load/ -v

test-red-team:
	pytest tests/red-team/ -v

test-accessibility:
	pytest tests/accessibility/ -v

# Code Quality
lint:
	ruff check .
	black --check .
	mypy services/

format:
	ruff check --fix .
	black .
	@echo "Code formatted successfully"

# Building
build-all:
	@for service in services/*; do \
		service_name=$$(basename $$service); \
		echo "Building $$service_name..."; \
		docker build -t ghcr.io/project-chimera/$$service_name:latest $$service; \
	done

build-service:
	@if [ -z "$(SERVICE)" ]; then \
		echo "Error: SERVICE parameter required"; \
		exit 1; \
	fi
	docker build -t ghcr.io/project-chimera/$(SERVICE):latest services/$(SERVICE)

# Deployment
deploy:
	@if [ -z "$(ENV)" ]; then \
		ENV="dev"; \
	fi
	./scripts/operations/deploy.sh $(ENV)

# Utilities
install-deps:
	./scripts/setup/install_dependencies.sh

verify:
	./scripts/setup/verify_environment.sh

check-env:
	@echo "Checking environment..."
	@command -v python3 >/dev/null || (echo "Python 3.10+ required"; exit 1)
	@command -v docker >/dev/null || (echo "Docker required"; exit 1)
	@command -v kubectl >/dev/null || (echo "kubectl required"; exit 1)
	@echo "Environment OK"

backup:
	./scripts/operations/backup.sh

restore:
	@if [ -z "$(BACKUP)" ]; then \
		echo "Error: BACKUP parameter required"; \
		./scripts/operations/backup.sh; \
		exit 1; \
	fi
	./scripts/operations/restore.sh $(BACKUP)

# CI/CD
ci:
	make lint
	make test-unit

cd-staging:
	make build-all
	./scripts/operations/deploy.sh staging

cd-production:
	make build-all
	./scripts/operations/deploy.sh production

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	rm -rf htmlcov/ .coverage
	@echo "Clean complete"

# Kubernetes
k8s-apply:
	kubectl apply -k infrastructure/kubernetes/overlays/dev

k8s-delete:
	kubectl delete -k infrastructure/kubernetes/overlays/dev

k8s-status:
	kubectl get all -n live
	kubectl get pods -n shared

# Training
train-lora:
	python scripts/training/train_lora.py \
		--base-model llama-2-7b-hf \
		--data-path data/theatrical_dialogue.jsonl \
		--output-dir models/lora-adapters/scenespeak-7b/v1.0.1

# Evaluation
evaluate:
	python models/evaluation/evaluate_perplexity.py \
		--model models/llama-2-7b \
		--test-file data/test_dialogues.txt

# Quick commands
run-openclaw:
	kubectl port-forward -n live svc/openclaw-orchestrator 8000:8000

run-scenespeak:
	kubectl port-forward -n live svc/scenespeak-agent 8001:8001

logs:
	kubectl logs -f -n live deployment/scenespeak-agent

logs-all:
	kubectl logs -f -n live --all-containers=true

# Shell access
shell-openclaw:
	kubectl exec -it -n live deployment/openclaw-orchestrator -- bash

shell-scenespeak:
	kubectl exec -it -n live deployment/scenespeak-agent -- bash

# Bootstrap
bootstrap:
	@echo "🚀 Bootstrapping Project Chimera..."
	@trap './scripts/bootstrap/cleanup-on-error.sh' ERR; \
	./scripts/bootstrap/01-install-k3s.sh && \
	./scripts/bootstrap/02-setup-registry.sh && \
	./scripts/bootstrap/03-build-images.sh && \
	./scripts/bootstrap/04-deploy-infrastructure.sh && \
	./scripts/bootstrap/05-deploy-monitoring.sh && \
	./scripts/bootstrap/06-deploy-services.sh && \
	./scripts/bootstrap/07-verify-deployment.sh
	@echo ""
	@echo "🎉 Bootstrap complete!"

bootstrap-status:
	@echo "📊 Bootstrap Status:"
	@kubectl get nodes 2>/dev/null || echo "k3s not installed"
	@kubectl get namespaces 2>/dev/null || echo "No namespaces"
	@kubectl get pods -n live 2>/dev/null || echo "No pods in live"
	@kubectl get pods -n shared 2>/dev/null || echo "No pods in shared"

bootstrap-destroy:
	@echo "⚠️  Destroying k3s cluster..."
	@read -p "Are you sure? This will remove k3s and all resources. (y/N): " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		pkill -f "port-forward" || true; \
		/usr/local/bin/k3s-uninstall.sh || true; \
		rm -f ~/.kube/config; \
		echo "🧹 k3s removed"; \
	else \
		echo "Aborted"; \
	fi
