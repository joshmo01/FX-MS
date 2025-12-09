# FX Smart Routing Engine - Makefile
# Author: Fintaar.ai

.PHONY: install dev test demo run lint clean docker help

# Default target
help:
	@echo "FX Smart Routing Engine - Available Commands"
	@echo "============================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install     - Install production dependencies"
	@echo "  make dev         - Install development dependencies"
	@echo ""
	@echo "Running:"
	@echo "  make run         - Start the API server"
	@echo "  make demo        - Run quick demo (key scenarios)"
	@echo "  make demo-full   - Run full demo (all scenarios)"
	@echo "  make demo-atomic - Run atomic swap demo"
	@echo ""
	@echo "Testing:"
	@echo "  make test        - Run all tests"
	@echo "  make test-cov    - Run tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint        - Run linters"
	@echo "  make format      - Format code"
	@echo ""
	@echo "Docker:"
	@echo "  make docker      - Build Docker image"
	@echo "  make docker-run  - Run Docker container"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean       - Remove build artifacts"

# Installation
install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black isort mypy

# Running
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

demo:
	python demo_all_routes.py --mode quick

demo-full:
	python demo_all_routes.py --mode full --export

demo-atomic:
	python demo_all_routes.py --mode atomic

demo-cbdc:
	python demo_all_routes.py --mode cbdc

demo-stable:
	python demo_all_routes.py --mode stable

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term

test-all:
	python tests/test_all_conversions.py

# Code Quality
lint:
	black --check app/ tests/
	isort --check-only app/ tests/
	mypy app/

format:
	black app/ tests/
	isort app/ tests/

# Docker
docker:
	docker build -t fx-smart-routing:latest .

docker-run:
	docker run -p 8000:8000 fx-smart-routing:latest

# Cleanup
clean:
	rm -rf __pycache__
	rm -rf app/__pycache__
	rm -rf app/**/__pycache__
	rm -rf tests/__pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
	rm -f demo_results.json

# GitHub Integration
github-prepare:
	chmod +x scripts/github_integration.sh
	./scripts/github_integration.sh
