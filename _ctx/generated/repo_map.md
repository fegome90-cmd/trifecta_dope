# Trifecta Dope - Repository Map

> **Generated**: __DATE__
> **Purpose**: High-level module navigation for ctx.plan code_navigation feature
> **Hash**: 3d77f3ef0fd1

---

## Module Overview

| Module | Path | Purpose | Entrypoints |
|--------|------|---------|-------------|
| Application | `src/application/` | Application layer | various |
| Domain | `src/domain/` | Domain layer | various |
| Infrastructure | `src/infrastructure/` | Infrastructure layer | various |


---

## Clean Architecture Layers

```
[Infrastructure Layer] - CLI, File System, Telemetry
        ↓
[Application Layer] - Use Cases, Business Logic
        ↓
[Domain Layer] - Core Entities, Business Rules
```

---

## CLI Commands Reference

### `ctx` App
```bash
trifecta ctx build     # Build context pack
trifecta ctx search    # Search chunks by query
trifecta ctx get       # Get chunks by ID
trifecta ctx sync      # Build + Validate
trifecta ctx stats     # Show telemetry statistics
trifecta ctx plan      # Generate execution plan
trifecta ctx eval-plan # Evaluate plan against dataset
```

---

## Key Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `skill.md` | Development rules and protocols |
| `_ctx/prime_*.md` | Progressive Context Compression index |
| `_ctx/session_*.md` | Session history |
| `_ctx/aliases.yaml` | Feature mapping for ctx.plan |
| `_ctx/telemetry/events.jsonl` | Telemetry event log |

---

**Limitations**: This is a curated map, not exhaustive indexing. For detailed symbol navigation, use ctx.plan with symbol_surface feature.

---

**PROMPT_FIX_HINT**: If you are an agent, copy NEXT_STEPS and rerun the original command. If still failing, paste stderr + command + exit code.
