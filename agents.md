# CLAUDE.md

This file provides guidance to code agents working with this repository.
It is agent-runtime specific and intentionally separate from `CLAUDE.md`.

---

## ⚠️ CRITICAL: READ THIS FIRST BEFORE ANY TASK

**DO NOT PROCEED WITH ANY TASK WITHOUT READING THESE CONTEXT FILES.**

Assuming anything about this project without consulting these files is a breach of the work contract.

### Agent Context Files (MANDATORY - READ THESE FIRST)

These files contain **CURRENT PROJECT STATE, ACTIVE FEATURES, AND ARCHITECTURE DECISIONS**. Ignoring them will result in:
- ✗ Breaking existing implementations
- ✗ Duplicating work already done
- ✗ Misunderstanding the current system state
- ✗ Failing verification gates

**READ IN THIS ORDER:**

0. **[skill.md](skill.md)** ← START HERE FIRST (3 min read)
   - **What**: Skills, roles, and core rules for this project
   - **Why**: Know the mandatory patterns and commands to use
   - **Contains**: Setup instructions, context cycle, session persistence
   - **CRITICAL**: Skip this → you'll use wrong commands and waste cycles

1. **[_ctx/agent_trifecta_dope.md](_ctx/agent_trifecta_dope.md)** ← THEN READ THIS (5 min read)
   - **What**: Current implementation status and active features
   - **Why**: Know what's ACTUALLY implemented vs. what's planned
   - **Contains**: Tech stack versions, active patterns, completed work
   - **CRITICAL**: Skip this → you'll duplicate work or break things

2. **[_ctx/session_trifecta_dope.md](_ctx/session_trifecta_dope.md)** ← THEN READ THIS (2 min skim)
   - **What**: Session history and continuation points
   - **Why**: Understand what was done in the last session
   - **Contains**: Previous decisions, known workarounds, open issues
   - **CRITICAL**: Skip this → you'll miss workarounds and hit known bugs

3. **[_ctx/prime_trifecta_dope.md](_ctx/prime_trifecta_dope.md)** ← REFERENCE THIS (1 min check)
   - **What**: Architectural reference and system structure
   - **Why**: Understand the fundamental system design
   - **Contains**: Core patterns, layer separation, dependency rules
   - **CRITICAL**: Skip this → you'll violate architectural constraints

### If You Skip These Files

⛔ **YOU WILL:**
- Propose features that already exist
- Break working implementations
- Violate architectural patterns
- Fail the verification gate
- Use wrong commands and waste tokens
- Waste time and tokens

✅ **INSTEAD:**
1. Read the 4 context files (11 min total)
2. Then start your task
3. Reference them constantly
4. Update session_trifecta_dope.md when you finish

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

### Repository Documentation
- **README.md** - Project overview, installation
- **docs/CONTRACTS.md** - API contracts, schemas
- **docs/CLI_WORKFLOW.md** - Official CLI usage
- **docs/adr/** - Architecture decision records
- **docs/backlog/** - Work Order system (WORKFLOW.md, OPERATIONS.md, TROUBLESHOOTING.md)

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

# Preflight (OBLIGATORY) - fail-closed validation before take
make wo-preflight WO=WO-XXXX

# Take WO (auto-creates branch + worktree)
uv run python scripts/ctx_wo_take.py WO-XXXX

# Navigate & work
cd .worktrees/WO-XXXX

# Complete WO (only via ctx_wo_finish.py)
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
- **[MANUAL_WO.md](docs/backlog/MANUAL_WO.md)** — Detallado del sistema de Work Orders (estados, DoD, cierre)

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
