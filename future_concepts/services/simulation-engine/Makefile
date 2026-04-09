.PHONY: help test run build deploy

help:
	@echo "Available commands:"
	@echo "  make test     - Run tests"
	@echo "  make run      - Run server"
	@echo "  make build    - Build Docker image"
	@echo "  make deploy   - Deploy to Kubernetes"

test:
	pytest tests/ -v --cov=. --cov-report=term

run:
	python main.py

build:
	docker build -t simulation-engine:latest .

deploy:
	kubectl apply -f k8s-deployment.yaml

validate:
	./scripts/validate_phase0.sh
