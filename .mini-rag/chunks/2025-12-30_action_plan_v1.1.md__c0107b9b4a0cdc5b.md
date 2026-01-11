### Implementation Steps

1. **Create new module**:
   ```python
   # src/infrastructure/validators.py
   """Segment validation logic (domain-pure)"""
   from dataclasses import dataclass
   from pathlib import Path
   from typing import List

   @dataclass(frozen=True)
   class ValidationResult:
       valid: bool
       errors: List[str]

   def validate_segment_structure(path: Path) -> ValidationResult:
       """[Move entire function from install_FP.py]"""
       # ...
   ```

2. **Update install_trifecta_context.py**:
   ```python
   # scripts/install_trifecta_context.py
   from src.infrastructure.validators import validate_segment

   def validate_segment(segment_path: Path) -> bool:
       result = validate_segment(segment_path)
       return result.valid
   ```

3. **Update test imports**:
   ```python
   # tests/installer_test.py
   from src.infrastructure.validators import validate_segment_structure
   ```

4. **Remove workaround**:
   - Delete `sys.path.insert()` from [tests/installer_test.py](tests/installer_test.py)
   - Keep `pythonpath` in [pyproject.toml](pyproject.toml) for scripts/ access only

5. **Verify**:
   ```bash
   uv run pytest tests/installer_test.py -v
   uv run mypy src/ --strict
   uv run ruff check .
   ```

---
