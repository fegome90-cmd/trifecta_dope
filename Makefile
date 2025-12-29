# Trifecta CLI Makefile
# Usage: make trifecta-create SEGMENT=my-segment PATH=path/to/segment SCOPE="Description"

.PHONY: trifecta-create trifecta-validate trifecta-refresh trifecta-help

# Default values
SEGMENT ?= my-segment
PATH ?= .
SCOPE ?= "Segment $(SEGMENT)"
SCAN_DOCS ?= 
PROFILE ?= impl_patch

# Trifecta CLI wrapper
TRIFECTA = ~/.local/bin/uv run python -m src.infrastructure.cli

trifecta-help:
	@echo "Trifecta CLI Commands:"
	@echo ""
	@echo "  make trifecta-create SEGMENT=<name> PATH=<dir> [SCOPE=<desc>] [SCAN_DOCS=<dir>] [PROFILE=<profile>]"
	@echo "  make trifecta-validate PATH=<dir>"
	@echo "  make trifecta-refresh PATH=<dir> SCAN_DOCS=<dir>"
	@echo ""
	@echo "Examples:"
	@echo "  make trifecta-create SEGMENT=memory-system PATH=hemdov/memory-system/ SCOPE='Memory management' SCAN_DOCS=hemdov/docs/"
	@echo "  make trifecta-validate PATH=eval/lime-harness/"
	@echo "  make trifecta-refresh PATH=eval/lime-harness/ SCAN_DOCS=eval/docs/"

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
