### Phase 1: Validator Module Creation (15 min)

```
1. Extract from scripts/install_FP.py:
   ├─ ValidationResult dataclass
   ├─ validate_segment_structure() function
   └─ All imports needed

2. Create src/infrastructure/validators.py:
   └─ Paste extracted code

3. Keep install_FP.py as reference (can deprecate later)
```

**File to Create**:
```
src/infrastructure/validators.py
├─ from dataclasses import dataclass
├─ from pathlib import Path
├─ from typing import List
├─
├─ @dataclass(frozen=True)
├─ class ValidationResult:
│   └─ valid: bool, errors: List[str]
│
└─ def validate_segment_structure(path: Path) -> ValidationResult:
   └─ [entire function from install_FP.py]
```
