# Design: Experiments Code Improvements

**Date:** 2026-03-10
**Status:** Approved
**Scope:** `experiments/` directory - Trifecta Cloud pgvector implementation

## Overview

Refactoring improvements identified during code review to address:
1. Duplicated code between files
2. Missing input validation
3. Redundant error handling patterns

## Changes

### 1. Extract Shared Module

**Problem:** `chunk_text_smart` duplicated verbatim in `02_ingest_docs.py` and `test_chunking.py`.

**Solution:** Create `experiments/chunking.py` module.

```python
"""Smart text chunking for document ingestion."""
import re

def chunk_text_smart(text: str, max_chars: int = 1500, overlap: int = 200) -> list[str]:
    """
    Chunking inteligente que respeta párrafos y oraciones.

    - Divide por párrafos primero
    - Si párrafo > max_chars, divide por oraciones
    - Si oración > max_chars, hace split duro con overlap
    - Añade overlap entre chunks para contexto
    """
    # ... implementation
```

**Impact:**
- `02_ingest_docs.py` → `from chunking import chunk_text_smart`
- `test_chunking.py` → `from chunking import chunk_text_smart`

### 2. Add Path Validation

**Problem:** `ingest_directory()` accepts arbitrary path without validation.

**Solution:** Add validation before processing.

```python
def ingest_directory(directory_path: str, segment_name: str):
    base_dir = Path(directory_path).resolve()

    # Validation
    if not base_dir.exists():
        raise ValueError(f"Directory does not exist: {base_dir}")
    if not base_dir.is_dir():
        raise ValueError(f"Path is not a directory: {base_dir}")

    # ... rest of function
```

### 3. Consolidate Error Handling

**Problem:** Duplicate try/except blocks for index creation.

**Solution:** Extract to helper function.

```python
def create_index_safely(cur, sql: str, description: str) -> None:
    """Execute index creation with sanitized error handling."""
    try:
        cur.execute(sql)
    except Exception as e:
        print(f"{description}: {sanitize_error(e, DATABASE_URL)}")
```

## File Changes

| File | Action | Lines Changed |
|------|--------|---------------|
| `experiments/chunking.py` | Create | ~65 lines |
| `experiments/02_ingest_docs.py` | Modify | ~10 lines |
| `experiments/04_test_prisma_db.py` | Modify | ~15 lines |
| `experiments/test_chunking.py` | Modify | ~5 lines |

## Testing

- Run `experiments/test_chunking.py` to verify chunking still works
- All 12 existing tests should pass
- No new tests required (behavior unchanged)

## Rollback

If issues arise:
1. Revert `02_ingest_docs.py` to include inline `chunk_text_smart`
2. Revert `test_chunking.py` to include inline `chunk_text_smart`
3. Delete `experiments/chunking.py`
