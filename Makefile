# Trifecta Dope Makefile
# v2.0 - Auditability & PCC Workflow

SHELL := /bin/bash
UV := uv run

.PHONY: help install start \
	test test-unit test-integration test-acceptance test-roadmap test-slow gate-all \
	wo-lint wo-lint-json wo-fmt wo-fmt-check \
	inarumen-check inarumen-fix \
	audit \
	ctx-sync ctx-search ctx-get ctx-stats \
	create

# Default Segment (current directory)
SEGMENT ?= .

help:
	@echo "Trifecta Dope v2.0"
	@echo "=================="
	@echo "Dev Lifecycle:"
	@echo "  make install          Install dependencies (uv sync)"
	@echo "  make gate-all         Run full acceptance gate (Unit + Int + Acceptance)"
	@echo "  make audit            Run comprehensive audit (Ola 5 style)"
	@echo ""
	@echo "Testing Gates:"
	@echo "  make test-unit"
	@echo "  make test-integration"
	@echo "  make test-acceptance       (default: -m 'not slow')"
	@echo "  make test-acceptance-slow  (includes @slow)"
	@echo "  make test-roadmap          (features in progress)"
	@echo ""
	@echo "WO Hygiene:"
	@echo "  make wo-lint               Lint WO YAML contracts (strict)"
	@echo "  make wo-lint-json          Lint WO YAML and output JSON findings"
	@echo "  make wo-fmt-check          Check canonical WO formatting"
	@echo "  make wo-fmt                Apply canonical WO formatting"
	@echo "  make inarumen-check        Run Inarumen gate (wo-fmt-check + wo-lint)"
	@echo "  make inarumen-fix          Run Inarumen fix flow (wo-fmt + wo-lint)"
	@echo ""
	@echo "Context Operations (PCC):"
	@echo "  make ctx-sync [SEGMENT=.]"
	@echo "  make ctx-search Q='query' [SEGMENT=.]"
	@echo "  make ctx-get IDS='id1,id2' [SEGMENT=.]"
	@echo "  make ctx-stats [SEGMENT=.]"
	@echo ""
	@echo "Scaffolding:"
	@echo "  make create SEGMENT=path/to/segment SCOPE='Description'"

# =============================================================================
# Development
# =============================================================================
install:
	uv sync

# =============================================================================
# Testing Gates
# =============================================================================
test-unit:
	$(UV) pytest -q tests/unit

test-integration:
	$(UV) pytest -q tests/integration

test-acceptance:
	$(UV) pytest -q tests/acceptance -m "not slow"

test-acceptance-slow:
	$(UV) pytest -q tests/acceptance -m "slow"

test-roadmap:
	$(UV) pytest -q tests/roadmap

wo-lint:
	$(UV) python scripts/ctx_wo_lint.py --strict

wo-lint-json:
	@$(UV) python scripts/ctx_wo_lint.py --json --strict

wo-fmt:
	$(UV) python scripts/ctx_wo_fmt.py --write

wo-fmt-check:
	$(UV) python scripts/ctx_wo_fmt.py --check

inarumen-check: wo-fmt-check wo-lint

inarumen-fix: wo-fmt wo-lint

gate-all: test-unit test-integration test-acceptance
	@echo "✅ GATE PASSED: Unit + Integration + Acceptance (Fast)"

audit: gate-all
	@echo "🔍 Auditing Code Quality..."
	@rg -n "pytest.skip" tests/acceptance && echo "❌ SKIP FOUND in Acceptance" && exit 1 || echo "✅ No Skips in Acceptance"
	@git diff --stat
	@echo "✅ AUDIT COMPLETE"

# =============================================================================
# Context Operations
# =============================================================================
ctx-sync:
	$(UV) trifecta ctx sync --segment $(SEGMENT)

ctx-search:
	$(UV) trifecta ctx search --segment $(SEGMENT) --query "$(Q)"

ctx-get:
	$(UV) trifecta ctx get --segment $(SEGMENT) --ids "$(IDS)"

ctx-stats:
	$(UV) trifecta ctx stats --segment $(SEGMENT)

# =============================================================================
# Scaffolding
# =============================================================================
create:
	@test -n "$(SEGMENT)" || (echo "SEGMENT is required"; exit 1)
	$(UV) trifecta create --segment $(SEGMENT) --scope "$(SCOPE)"
