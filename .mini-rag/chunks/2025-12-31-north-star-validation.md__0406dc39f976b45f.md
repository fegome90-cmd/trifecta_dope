### Task 3: Integrar Gate FP en CLI

**Files:**
- Modify: `src/infrastructure/cli.py`

**Step 3.1: Write the failing test**

```python
# tests/unit/test_cli_fp_gate.py
import subprocess
from pathlib import Path

class TestCLIFPGate:
    def test_ctx_build_uses_fp_validation(self, tmp_path: Path) -> None:
        """ctx build should use FP validation and fail cleanly."""
        segment = tmp_path / "bad_fp_seg"
        segment.mkdir()
        
        result = subprocess.run(
            ["uv", "run", "trifecta", "ctx", "build", "--segment", str(segment)],
            capture_output=True, text=True
        )
        
        assert result.returncode != 0
        assert "validation" in result.stdout.lower() or "error" in result.stdout.lower()
```

**Step 3.2: Run test**

Run: `uv run pytest tests/unit/test_cli_fp_gate.py -v`
Expected: FAIL (currently no early exit)

**Step 3.3: Implement FP Gate in CLI**
