#!/usr/bin/env just --justfile
# ==========================================
# DEFAULT
# ==========================================

# Show all available commands
@default:
	just --list

# ==========================================
# DEVELOPMENT
# ==========================================

# Run ruff linter
lint:
	ruff check .

# Run ruff formatter (diff mode — see what would change)
format-check:
	ruff format --check .

# Auto-format with ruff
format:
	ruff format .

# Run yamllint
yaml-lint:
	yamllint .

# Run all pre-commit hooks
pre-commit:
	prek run --all-files

# Run full CI pipeline (lint + format-check + yaml-lint)
ci: lint format-check yaml-lint test

# Install pre-commit git hooks
hooks-install:
	prek install

# ==========================================
# TESTING
# ==========================================

# Run test suite
test:
	python3 -m pytest tests/ -v

# Run tests with coverage
coverage:
	python3 -m pytest tests/ -v --cov=custom_components.surfcaster --cov-report=term-missing

# ==========================================
# HACS VALIDATION
# ==========================================

# Run HACS validation locally
hacs-validate:
	python3 -m custom_components.surfcaster.validate
