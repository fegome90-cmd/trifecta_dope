### 2. FP Validator Wrapper (`src/infrastructure/validators.py`)

Wraps pure validation logic (`validate_segment_structure`) into the Result Monad context.

- Returns `Ok(ValidationResult)` or `Err(list[str])`.
- Enables safe composition.
