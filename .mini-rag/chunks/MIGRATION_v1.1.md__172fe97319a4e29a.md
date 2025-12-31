### install_FP.py → Stable Installer (v1.1+)

**Status**: ✅ STABLE - Use this script for all installations

**Features**:
- Clean Architecture imports from `src/infrastructure/validators`
- Path-aware deduplication (nested skill.md files supported)
- Type-safe ValidationResult (frozen dataclass)
- Compatible with pytest + mypy strict

**Usage**:
```bash
uv run python scripts/install_FP.py --segment /path/to/segment
```

**Architecture**:
```
scripts/install_FP.py (imperative shell)
    ↓ imports
src/infrastructure/validators.py (domain logic)
    ├─ ValidationResult (frozen dataclass)
    └─ validate_segment_structure(path) → ValidationResult
```

---
