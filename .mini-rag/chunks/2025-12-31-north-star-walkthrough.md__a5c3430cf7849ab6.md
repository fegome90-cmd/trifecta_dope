### 1. Result Monad (`src/domain/result.py`)

Pure domain type for Railway Oriented Programming.

- **Immutable**: Frozen dataclasses (`Ok[T]`, `Err[E]`).
- **No Exceptions**: Enforces error handling via types.
- **Type-Safe**: `mypy --strict` compliant.
