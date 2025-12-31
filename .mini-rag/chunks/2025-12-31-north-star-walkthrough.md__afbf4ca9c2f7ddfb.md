### 3. CLI Gate Integration (`src/infrastructure/cli.py`)

Pattern matching replaces try/except blocks.

```python
match validate_segment_fp(path):
    case Err(errors):
        # ... logic ...
        raise typer.Exit(code=1)
    case Ok(_):
        # Proceed to Contract Checks
```

---
