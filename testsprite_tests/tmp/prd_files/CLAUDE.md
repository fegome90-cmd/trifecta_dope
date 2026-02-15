# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
It is Claude-specific; `agents.md` serves other agent runtimes.

---

## Quick Start

```bash
# Install
uv sync --all-groups

# Run CLI
uv run trifecta --help

# Tests
uv run pytest                    # All tests
uv run pytest -m "not slow"      # Skip slow tests
uv run pytest tests/acceptance/  # Acceptance gate

# Type check & lint
uv run mypy src/ --strict
uv run ruff check src/
uv run ruff format src/
```

---

## Architecture Overview

**Python + Clean Architecture** with strict layer separation:

- **Domain** (`src/domain/`) - Pure business logic (no IO, no async, no framework dependencies)
- **Application** (`src/application/`) - Use cases, orchestration
- **Infrastructure** (`src/infrastructure/`) - Framework adapters, IO, external services

**Critical Rule:** Dependencies point INWARD. Domain → Application → Infrastructure.

See `docs/CONTRACTS.md` and architecture docs in `docs/adr/` for complete patterns.

---

## Key Patterns

- **Frozen dataclasses** for domain entities (immutable)
- **Pure functions** in domain services (testable without mocks)
- **Protocols** for infrastructure interfaces (ports/adapters)
- **Result types** for error handling (`Ok[T] | Err[E]`)
- **Telemetry** for observability (no side-effect in tests via `TRIFECTA_NO_TELEMETRY`)

---

## Development Workflow

- **TDD**: Write tests BEFORE implementation (RED → GREEN → REFACTOR)
- **Domain first**: Business logic is pure and tested in isolation
- **Use `uv`**: Package management and task runner
- **Pre-commit hooks**: Auto-run tests on commit (bypass with `--no-verify` if needed)

---

## Red Flags

| Violation | Why It's Wrong | Fix |
|-----------|----------------|-----|
| IO in domain | Domain must be pure | Move to infrastructure adapter |
| Async in domain | Domain is synchronous | Move to application/infra |
| Pydantic in domain | Framework coupling | Use frozen dataclasses |
| Untested pure functions | Easy to test, no excuse | Write unit tests |
| Hardcoded paths | Portability issues | Use `repo_root()` helper |

---

## Testing

- **Unit tests** (`tests/unit/`) - Domain logic, pure functions
- **Integration tests** (`tests/integration/`) - Use cases with real adapters
- **Acceptance tests** (`tests/acceptance/`) - Black-box CLI tests (gate: `-m "not slow"`)
- **Roadmap tests** (`tests/roadmap/`) - Future features (isolated, `--ignore`)

**Coverage target**: ≥80% branch coverage

---

## Source of Truth

- **README.md** - Project overview, installation
- **docs/CONTRACTS.md** - API contracts, schemas
- **docs/CLI_WORKFLOW.md** - Official CLI usage
- **docs/adr/** - Architecture decision records
- **docs/backlog/** - Work Order system (WORKFLOW.md, OPERATIONS.md, TROUBLESHOOTING.md)
- **_ctx/agent_trifecta_dope.md** - Active features, tech stack
- **_ctx/session_trifecta_dope.md** - Session history, runbook

---

## Trifecta-Specific Rules

### _ctx/ Directory Conventions
- **_ctx/logs/**: ONLY .log files (command stdout/stderr). Use /tmp/ for intermediate .md files.
- **When updating session.md**: Create temp in /tmp/, append with `cat`, then cleanup. Never store .md in _ctx/logs/.

### Context Pack Workflow
1. `trifecta create --segment .` - Bootstrap metadata
2. `trifecta ctx sync --segment .` - Build context pack
3. `trifecta ctx validate --segment .` - Verify integrity
4. `trifecta ctx search --segment . --query "..."` - Search
5. `trifecta ctx get --segment . --ids "..."` - Retrieve chunks

### Environment & Ops
- **Scope Separation**: `pyproject.toml` / `pytest-env` is for **Tests**. `.envrc` (direnv) is for **Dev CLI**.
- **Default Enablement**: Must be verified via CLI *without* env var prefixes.
- **Audit-Grade Gates**: `exit 0` is not enough. Verify internal state (telemetry backend, file creation).
- **Rollback**: Must be verifiable in <5 minutes via env var override.

---

## Work Orders (WO System)

The WO system provides isolated development environments using git worktrees.

### Quick Workflow

```bash
# List pending WOs
uv run python scripts/ctx_wo_take.py --list

# Take WO (auto-creates branch + worktree)
uv run python scripts/ctx_wo_take.py WO-XXXX

# Navigate & work
cd .worktrees/WO-XXXX

# Complete WO
uv run python scripts/ctx_wo_finish.py WO-XXXX
```

### Key Scripts

| Script | Purpose |
|--------|---------|
| `ctx_wo_take.py` | Take WO with auto branch/worktree creation |
| `ctx_wo_finish.py` | Complete WO with DoD validation |
| `helpers.py` | Core utilities (worktree, lock, branch) |
| `ctx_reconcile_state.py` | Repair state inconsistencies |

### Structure & State Machine

```
_ctx/jobs/
├── pending/*.yaml    → [take] → running/*.yaml → [finish] → done/*.yaml
└── failed/*.yaml
```

**States**: pending → running → done (or failed)

### Worktree Management

- **Branch**: `feat/wo-WO-XXXX` (from `main`)
- **Path**: `.worktrees/WO-XXXX`
- **Lock**: `_ctx/jobs/running/WO-XXXX.lock` (atomic, stale >1h auto-cleaned)

```bash
git worktree list              # List worktrees
git worktree remove .worktrees/WO-XXXX  # Cleanup
```

### Detailed Documentation

- **[WORKFLOW.md](docs/backlog/WORKFLOW.md)** — Complete lifecycle guide
- **[OPERATIONS.md](docs/backlog/OPERATIONS.md)** — Daily operations playbook
- **[TROUBLESHOOTING.md](docs/backlog/TROUBLESHOOTING.md)** — Common issues
- **[README.md](docs/backlog/README.md)** — Quick reference

---

## Telemetry

- **Production**: Events logged to `_ctx/telemetry/events.jsonl`
- **Testing**: Use `TRIFECTA_NO_TELEMETRY=1` for zero side-effects
- **Pre-commit**: Auto-redirects telemetry via `TRIFECTA_TELEMETRY_DIR`

---

## Common Tasks

```bash
# Create new segment
uv run trifecta create --segment /path/to/project

# Sync context
uv run trifecta ctx sync --segment .

# Search + get workflow
uv run trifecta ctx search --segment . --query "ErrorCard" --limit 5
uv run trifecta ctx get --segment . --ids "prime:abc123" --mode excerpt

# AST symbols (M1)
uv run trifecta ast symbols "sym://python/mod/src.domain.result" --segment .

# Run gate
bash scripts/gate_clean_worktree_repro.sh  # WO-0007 reproducibility
```

---

**Living Document**: Update this file when friction is encountered or new patterns emerge.
