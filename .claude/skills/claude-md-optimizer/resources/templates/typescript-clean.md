# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Quick Start

```bash
# Type checking
npm run typecheck

# Run tests
npm test

# Build
npm run build

# Development
npm run dev
```

---

## Architecture Overview

**TypeScript + Clean Architecture** with strict layer separation.

**Critical Rule:** Dependencies point INWARD only. Domain never imports from infrastructure.

See `ARCHITECTURE.md` for complete layer rules and patterns.

---

## Key Patterns

- **Result Type**: `Result<T, E>` for functional error handling
- **Branded Types**: Type-safe IDs (`VideoId`, `ChannelId`)
- **Pure Functions**: All domain logic in `src/domain/services/` is pure and synchronous

---

## Development Workflow

1. Start with `PRP.md` for requirements
2. Write domain entities first (pure, frozen interfaces)
3. Write pure functions in `domain/services/`
4. Write infrastructure in `infrastructure/` (IO only)
5. Tests for domain need no mocks

---

## Red Flags

| Violation | Why It's Wrong |
|-----------|----------------|
| Domain imports infrastructure | Breaks dependency rule |
| Async in domain | Domain must be pure and synchronous |
| Direct Playwright in domain | IO belongs in infrastructure only |
| `any` types (except branded casting) | Loses type safety |

---

## Source of Truth

- **PRP.md** - Product requirements and constraints
- **ARCHITECTURE.md** - Detailed architecture patterns
- **README.md** - Project overview
