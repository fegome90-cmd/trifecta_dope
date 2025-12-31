### Task 2: Refactorizar validate_segment_structure a FP

**Files:**
- Modify: `src/infrastructure/validators.py`

**Step 2.1: Write the failing test**

```python
# tests/unit/test_validators_fp.py
import pytest
from pathlib import Path
from src.infrastructure.validators import validate_segment_fp
from src.domain.result import Ok, Err

class TestValidatorFP:
    def test_valid_segment_returns_ok(self, tmp_path: Path) -> None:
        seg = tmp_path / "valid_seg"
        seg.mkdir()
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "agent_valid_seg.md").touch()
        (ctx / "prime_valid_seg.md").touch()
        (ctx / "session_valid_seg.md").touch()

        result = validate_segment_fp(seg)

        assert result.is_ok(), f"Expected Ok, got Err: {result}"

    def test_invalid_segment_returns_err(self, tmp_path: Path) -> None:
        seg = tmp_path / "invalid_seg"
        seg.mkdir()
        # Missing everything

        result = validate_segment_fp(seg)

        assert result.is_err(), "Expected Err for invalid segment"
        errors = result.unwrap_err()
        assert len(errors) > 0
```

**Step 2.2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_validators_fp.py -v`
Expected: FAIL (ImportError: cannot import validate_segment_fp)

**Step 2.3: Implement validate_segment_fp**
