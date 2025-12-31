# Trifecta Dope - Repository Map

> **Generated**: 2025-12-31
> **Purpose**: High-level module navigation for ctx.plan code_navigation feature

---

## Module Overview

| Module | Path | Purpose | Entrypoints |
|--------|------|---------|-------------|
| CLI | `src/infrastructure/cli.py` | Typer CLI commands | `ctx` app, `load` command |
| Domain | `src/domain/` | Core business entities | `context_models.py` |
| Application | `src/application/` | Use cases | `use_cases.py`, `search_get_usecases.py`, `plan_use_case.py` |
| Infrastructure | `src/infrastructure/` | External adapters | `cli.py`, `telemetry.py`, `file_system.py` |
| Scripts | `scripts/` | Utility scripts | `telemetry_diagnostic.py`, `evaluate_plan.py` |

---

## Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Interfaces (Dependency Injection)                          │
│  src/hemdov/interfaces/  (not in this repo)                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Application Layer (Use Cases - Business Logic)             │
│  - BuildContextPackUseCase: Build context packs             │
│  - SearchUseCase: Search chunks by query                    │
│  - GetChunksUseCase: Retrieve chunks by ID                  │
│  - StatsUseCase: Generate telemetry statistics              │
│  - PlanUseCase: Generate execution plan (PRIME-only)        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Domain Layer (Core Entities - No Dependencies)             │
│  - ContextPack, Chunk, Index models                         │
│  - Business rules for context management                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Infrastructure Layer (Adapters - External Services)        │
│  - Typer CLI                                                │
│  - File system access                                       │
│  - Telemetry (JSONL logging)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## CLI Commands Reference

### `ctx` App
```bash
trifecta ctx build     # Build context pack
trifecta ctx search    # Search chunks by query
trifecta ctx get       # Get chunks by ID
trifecta ctx sync      # Sync context pack
trifecta ctx validate  # Validate context pack
trifecta ctx stats     # Show telemetry statistics
trifecta ctx plan      # Generate execution plan (PRIME-only)
trifecta ctx eval-plan # Evaluate plan against dataset
```

### `load` Command
```bash
trifecta load          # Load macro from context pack
```

---

## Key Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `skill.md` | Development rules and protocols |
| `RELEASE_NOTES_v1.md` | Version history |
| `_ctx/prime_*.md` | Progressive Context Compression index |
| `_ctx/session_*.md` | Session history |
| `_ctx/aliases.yaml` | Feature mapping for ctx.plan |
| `_ctx/telemetry/events.jsonl` | Telemetry event log |

---

## Navigation Strategy

1. **For architecture questions**: Start with README.md → PRIME
2. **For implementation**: Start with use_cases.py → specific module
3. **For CLI commands**: Start with cli.py → relevant use case
4. **For data**: Check telemetry events.jsonl
5. **For symbols**: Use prime index (full AST/LSP planned for v2)

---

**Limitations**: This is a curated map, not exhaustive indexing. For detailed symbol navigation, use ctx.plan with symbol_surface feature.
