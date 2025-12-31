```python
# In src/infrastructure/validators.py - Add new FP version

from src.domain.result import Ok, Err, Result

def validate_segment_fp(path: Path) -> Result[ValidationResult, list[str]]:
    """
    FP version of validate_segment_structure.
    
    Returns:
        Ok(ValidationResult) if valid
        Err(list[str]) with error messages if invalid
    """
    # Delegate to existing pure function
    result = validate_segment_structure(path)
    
    if result.valid:
        return Ok(result)
    else:
        return Err(result.errors)
```

**Step 2.4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_validators_fp.py -v`
Expected: PASS

**Step 2.5: Commit**

```bash
git add src/infrastructure/validators.py tests/unit/test_validators_fp.py
git commit -m "feat(validators): Add FP wrapper returning Result monad"
```

---
