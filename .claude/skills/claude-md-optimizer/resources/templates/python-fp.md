# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Quick Start

```bash
# Run with uv
uv run python main.py

# Tests
uv run pytest

# Type check
uv run mypy src/

# Format
uv run ruff check src/
uv run ruff format src/
```

---

## Architecture Overview

**Python + Functional Programming** with pure core/impure edge separation.

**Critical Rule:** Domain layer is pure (no IO, no async, no side effects). All IO operations in infrastructure layer.

See `ARCHITECTURE.md` for complete patterns.

---

## Key Patterns

- **Frozen dataclasses** for entities (immutable data)
- **Pure functions** in domain services (no side effects)
- **Ports/Protocols** for infrastructure interfaces
- **Result types** for error handling (`returns.Result`)

---

## Development Workflow

- **TDD**: RED → GREEN → REFACTOR
- Write tests first, domain first
- Use `uv` for package management
- Keep domain pure and testable without mocks

---

## Red Flags

| Violation | Why It's Wrong |
|-----------|----------------|
| IO in domain | Domain must be pure |
| Untested pure functions | Easy to test, no excuse |
| Pydantic in domain | Frameworks belong in infrastructure |
| Async in domain | Domain must be synchronous |

---

## Source of Truth

- **PRP.md** - Product requirements
- **ARCHITECTURE.md** - Architecture patterns
- **README.md** - Project overview
