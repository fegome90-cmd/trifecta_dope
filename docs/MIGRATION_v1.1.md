# Migration Guide v1.1

## Script Consolidation

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

### install_trifecta_context.py → DEPRECATED

**Status**: ⚠️ DEPRECATED - Kept for backward compatibility only

**Reason**: Does not follow Clean Architecture patterns (no domain layer separation)

**Migration**:
Replace all usages of:
```bash
python scripts/install_trifecta_context.py --cli-root . --segment /path
```

With:
```bash
python scripts/install_FP.py --segment /path
```

**Note**: `install_trifecta_context.py` will be removed in v2.0

---

## Deduplication Logic Changes

### Before v1.1 (Naive)
```python
# Filename-based exclusion (BROKEN for nested files)
REFERENCE_EXCLUSION = {"skill.md"}
if name in REFERENCE_EXCLUSION:
    continue  # ❌ Excludes docs/library/skill.md incorrectly
```

### After v1.1 (Path-Aware)
```python
# Path-based exclusion using resolve()
primary_skill_path = target_path / "skill.md"
excluded_paths = {primary_skill_path.resolve()}

for name, path in refs.items():
    if path.resolve() in excluded_paths:
        continue  # ✅ Only excludes root skill.md
```

**Impact**:
- Root `skill.md` deduplicated ✅
- Nested `library/python/skill.md` indexed as `ref:` ✅
- Context pack: 6 chunks (was 7), -646 tokens saved

---

## Test Coverage

### New Tests (v1.1)
- `test_nested_skill_md_is_NOT_excluded` - Validates nested skill library support
- Path-aware deduplication contracts updated

### Test Results
- **Before**: 15/15 PASS (naive logic)
- **After**: 16/16 PASS (path-aware + nested test)
- **Integration**: 82/82 PASS (full test suite)

---

## Breaking Changes

None. All changes are backward compatible.

The deprecated `install_trifecta_context.py` still works but will emit warnings in future versions.

---

## Recommended Actions

1. **Update CI/CD pipelines**: Replace `install_trifecta_context.py` with `install_FP.py`
2. **Update documentation**: Reference `install_FP.py` in setup guides
3. **Validate segments**: Run `pytest tests/unit/test_validators.py -v` to verify migration
4. **Sync context packs**: Execute `trifecta ctx sync --segment .` to regenerate with new logic

---

## Questions?

See [2025-12-30_action_plan_v1.1.md](plans/2025-12-30_action_plan_v1.1.md) for technical details.
