.PHONY: help install install-dev test test-cov test-watch lint format clean build dev release

# Default target
.DEFAULT_GOAL := help

# Color output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Project variables
PYTHON := python3
UV := uv
PYTEST := pytest
RUFF := ruff

help: ## Show this help message
	@echo "$(BLUE)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ============================================================================
# Development Environment Setup
# ============================================================================

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(UV) pip install -e .

install-dev: ## Install development dependencies (includes test dependencies)
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(UV) pip install -e ".[dev]"
	@echo "$(GREEN)✓ Development environment ready$(NC)"

venv: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(UV) venv
	@echo "$(GREEN)✓ Virtual environment created$(NC)"
	@echo "$(YELLOW)Activate with: source .venv/bin/activate$(NC)"

# ============================================================================
# Testing
# ============================================================================

test: ## Run unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(PYTEST) tests/ -v

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(PYTEST) tests/ -v --cov=RomM --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	$(PYTEST) tests/ -v --looponfail

test-platform-maps: ## Run only platform_maps tests
	@echo "$(BLUE)Running platform_maps tests...$(NC)"
	$(PYTEST) tests/test_platform_maps.py -v

test-quick: ## Run tests without coverage (faster)
	@echo "$(BLUE)Running quick tests...$(NC)"
	$(PYTEST) tests/ -v --no-cov

# ============================================================================
# Code Quality
# ============================================================================

lint: ## Run linter (ruff check)
	@echo "$(BLUE)Running linter...$(NC)"
	$(RUFF) check RomM/ tests/

lint-fix: ## Run linter and auto-fix issues
	@echo "$(BLUE)Running linter with auto-fix...$(NC)"
	$(RUFF) check --fix RomM/ tests/

format: ## Format code with ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	$(RUFF) format RomM/ tests/
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check code formatting without modifying
	@echo "$(BLUE)Checking code formatting...$(NC)"
	$(RUFF) format --check RomM/ tests/

check: lint format-check test ## Run all checks (lint + format + test)
	@echo "$(GREEN)✓ All checks passed$(NC)"

# ============================================================================
# Build & Package
# ============================================================================

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf .build .dist
	rm -rf __pycache__ RomM/__pycache__ tests/__pycache__
	rm -rf .pytest_cache htmlcov .coverage
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Cleaned$(NC)"

build: clean ## Build for development (uses justfile)
	@echo "$(BLUE)Building for development...$(NC)"
	just clean copy build-dev
	@echo "$(GREEN)✓ Development build complete$(NC)"

release: clean ## Build production release (uses justfile)
	@echo "$(BLUE)Building production release...$(NC)"
	just release
	@echo "$(GREEN)✓ Production release complete$(NC)"

# ============================================================================
# Development Workflows
# ============================================================================

dev: install-dev ## Setup development environment and run tests
	@echo "$(BLUE)Setting up development environment...$(NC)"
	$(MAKE) test
	@echo "$(GREEN)✓ Development environment ready and tested$(NC)"

watch: ## Watch for changes and run tests automatically
	@echo "$(BLUE)Watching for changes...$(NC)"
	$(PYTEST) tests/ -v --looponfail

pre-commit: format lint test ## Run pre-commit checks (format, lint, test)
	@echo "$(GREEN)✓ Pre-commit checks passed$(NC)"

# ============================================================================
# Deployment
# ============================================================================

upload: ## Upload to device (uses justfile)
	@echo "$(BLUE)Uploading to device...$(NC)"
	just upload

upload-update: ## Upload update to device (uses justfile)
	@echo "$(BLUE)Uploading update to device...$(NC)"
	just upload-update

# ============================================================================
# Information & Documentation
# ============================================================================

info: ## Show project information
	@echo "$(BLUE)Project Information:$(NC)"
	@echo "  Name:         muos-app"
	@echo "  Version:      0.5.0"
	@echo "  Python:       $(shell $(PYTHON) --version)"
	@echo "  UV:           $(shell $(UV) --version 2>/dev/null || echo 'not installed')"
	@echo "  Pytest:       $(shell $(PYTEST) --version 2>/dev/null || echo 'not installed')"
	@echo "  Ruff:         $(shell $(RUFF) --version 2>/dev/null || echo 'not installed')"

deps: ## Show dependency tree
	@echo "$(BLUE)Dependency tree:$(NC)"
	$(UV) pip list

coverage-html: test-cov ## Open coverage report in browser
	@echo "$(BLUE)Opening coverage report...$(NC)"
	@open htmlcov/index.html || xdg-open htmlcov/index.html 2>/dev/null || echo "Please open htmlcov/index.html manually"

# ============================================================================
# Quick Aliases
# ============================================================================

t: test ## Alias for 'test'
tc: test-cov ## Alias for 'test-cov'
l: lint ## Alias for 'lint'
f: format ## Alias for 'format'
c: clean ## Alias for 'clean'
i: install-dev ## Alias for 'install-dev'
