### Solution (Minimal)

**Option A: Move to src/ (Correct)**
```
src/infrastructure/
├── validators.py  [NEW]
│   └─ validate_segment_structure()
│       └─ ValidationResult dataclass
│       └─ Dynamic naming validation
│
scripts/
├── install_trifecta_context.py  [REFACTORED]
│   └─ Import from: from src.infrastructure.validators import validate_segment
│   └─ Remove logic, keep CLI interface
```

**Option B: Keep in scripts/, add __init__.py (Quick Fix)**
- Make `scripts/` a package
- Import: `from scripts.install_FP import validate_segment_structure`
- Impact: Acceptable for MVP, but not ideal long-term

**Recommendation**: **Option A** (aligns with Clean Architecture).
