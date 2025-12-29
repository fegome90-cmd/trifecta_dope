# Trifecta CLI Makefile
# Usage: make trifecta-create SEGMENT=my-segment PATH=path/to/segment SCOPE="Description"

SHELL := /bin/bash

.PHONY: trifecta-create trifecta-validate trifecta-refresh trifecta-help \
	minirag-help minirag-setup minirag-init minirag-index minirag-query minirag-doctor

# Default values
SEGMENT ?= my-segment
PATH ?= .
SCOPE ?= "Segment $(SEGMENT)"
SCAN_DOCS ?=
PROFILE ?= impl_patch

# Trifecta CLI wrapper
TRIFECTA = ~/.local/bin/uv run python -m src.infrastructure.cli

# Mini-RAG defaults (override as needed)
MINIRAG_SOURCE ?= $(HOME)/Developer/Minirag
MINIRAG_QUERY ?= "PCC"

trifecta-help:
	@echo "Trifecta CLI Commands:"
	@echo ""
	@echo "  make trifecta-create SEGMENT=<name> PATH=<dir> [SCOPE=<desc>] [SCAN_DOCS=<dir>] [PROFILE=<profile>]"
	@echo "  make trifecta-validate PATH=<dir>"
	@echo "  make trifecta-refresh PATH=<dir> SCAN_DOCS=<dir>"
	@echo ""
	@echo "Mini-RAG Commands:"
	@echo "  make minirag-setup [MINIRAG_SOURCE=<path>]"
	@echo "  make minirag-init"
	@echo "  make minirag-index"
	@echo "  make minirag-query [MINIRAG_QUERY='your question']"
	@echo "  make minirag-doctor"
	@echo ""
	@echo "Examples:"
	@echo "  make trifecta-create SEGMENT=memory-system PATH=hemdov/memory-system/ SCOPE='Memory management' SCAN_DOCS=hemdov/docs/"
	@echo "  make trifecta-validate PATH=eval/lime-harness/"
	@echo "  make trifecta-refresh PATH=eval/lime-harness/ SCAN_DOCS=eval/docs/"
	@echo "  make minirag-setup MINIRAG_SOURCE=~/Developer/Minirag"
	@echo "  make minirag-query MINIRAG_QUERY='programming context caller'"

trifecta-create:
	@echo "Creating Trifecta pack for $(SEGMENT)..."
	$(TRIFECTA) create \
		--segment $(SEGMENT) \
		--path $(PATH) \
		--scope "$(SCOPE)" \
		--profile $(PROFILE) \
		$(if $(SCAN_DOCS),--scan-docs $(SCAN_DOCS),)

trifecta-validate:
	@echo "Validating Trifecta at $(PATH)..."
	$(TRIFECTA) validate --path $(PATH)

trifecta-refresh:
	@echo "Refreshing prime at $(PATH)..."
	$(TRIFECTA) refresh-prime --path $(PATH) --scan-docs $(SCAN_DOCS)

minirag-help:
	@echo "Mini-RAG quick usage:"
	@echo "  make minirag-setup MINIRAG_SOURCE=<path>"
	@echo "  make minirag-index"
	@echo "  make minirag-query MINIRAG_QUERY='your question'"

minirag-setup:
	@echo "Installing Mini-RAG from $(MINIRAG_SOURCE)..."
	python $(MINIRAG_SOURCE)/install_improved.py --source $(MINIRAG_SOURCE)

minirag-init:
	@echo "Initializing Mini-RAG..."
	. .venv/bin/activate && mini-rag init

minirag-index:
	@echo "Indexing Mini-RAG documents..."
	. .venv/bin/activate && mini-rag index

minirag-query:
	@echo "Querying Mini-RAG..."
	. .venv/bin/activate && mini-rag query $(MINIRAG_QUERY)

minirag-doctor:
	@echo "Running Mini-RAG doctor..."
	. .venv/bin/activate && mini-rag doctor
