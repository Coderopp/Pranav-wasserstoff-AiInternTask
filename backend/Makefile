.PHONY: help install install-dev test test-cov lint format type-check security clean run docs

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  lint         - Run linting (flake8)"
	@echo "  format       - Format code (black + isort)"
	@echo "  type-check   - Run type checking (mypy)"
	@echo "  security     - Run security checks (bandit + safety)"
	@echo "  clean        - Clean cache and build files"
	@echo "  run          - Run the development server"
	@echo "  docs         - Generate documentation"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

# Testing
test:
	pytest

test-cov:
	pytest --cov=app --cov-report=html --cov-report=term

# Code quality
lint:
	flake8 app tests

format:
	black app tests
	isort app tests

type-check:
	mypy app

security:
	bandit -r app
	safety check

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

# Development server
run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Documentation
docs:
	cd docs && make html

# All checks (useful for CI/CD)
check: lint type-check security test

# Development setup
setup: install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make run' to start the development server"