# Code Review Report: src/domain

**Date:** 2026-01-06
**Scope:** `src/domain` directory
**Reviewer:** Antigravity (Superpower V)
**Verdict:** 🔴 **FAIL** (Critical Architecture Violations)

## 🚨 Critical Issues (Must Fix)

### 1. Infrastructure Leak in Domain
**File:** `src/domain/ast_cache.py`
**Violation:** Domain layer performs direct I/O and depends on `sqlite3`.
**Rule:** `Domain` must be pure business logic. IO/Persistence belongs in `Infrastructure`.
**Evidence:**
```python
class SQLiteCache:
    def _init_db(self):
        import sqlite3  # <--- CRITICAL
        self.db_path.parent.mkdir(...)
```
**Remediation:**
- Move `SQLiteCache` class to `src/infrastructure/adapters/sqlite_cache.py`.
- Keep `AstCache` (Protocol) and `CacheStatus`/`CacheEntry` (Data classes) in `src/domain`.

### 2. Framework Coupling
**File:** `src/domain/models.py`
**Violation:** Domain entities inherit from `pydantic.BaseModel`.
**Rule:** Domain entities should be framework-agnostic (Vanilla Python or `@dataclass`).
**Evidence:**
```python
from pydantic import BaseModel
class TrifectaConfig(BaseModel): ...
```
**Remediation:**
- Convert `TrifectaConfig`, `TrifectaPack`, `ValidationResult` to `@dataclass(frozen=True)`.
- If validation is needed, use a `Validator` service or factory method, or keep Pydantic models in `src/application/schemas`.

## ⚠️ Important Issues (Should Fix)

- **Mixed Abstraction Levels**: `ast_cache.py` mixes high-level Protocol definitions with low-level SQL queries.

## ✅ Good Points

- `anchor_extractor.py` implements pure logic correctly.
- `result.py` provides a clean Monad pattern for error handling.
- Naming conventions are generally consistent.

## Action Plan (Next Steps)

1. **Refactor CACHE**:
   - Create `src/infrastructure/cache/`.
   - Move `SQLiteCache` implementation there.
   - Update DI container to inject `SQLiteCache` where `AstCache` is required.

2. **Refactor MODELS**:
   - Convert `TrifectaConfig` to frozen dataclass.
   - Move Pydantic validation logic to Application layer (Use Cases) or Infrastructure (CLI parsing).

---
*Generated via Superpower: code-review-checklist*
