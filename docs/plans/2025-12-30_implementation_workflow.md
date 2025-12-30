# v1.1 Implementation Sprint - Visual Roadmap

## Current Architecture (BEFORE v1.1)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ CURRENT STRUCTURE (Clean Architecture Violation)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  scripts/                                                                │
│  ├─ install_FP.py                                                       │
│  │  └─ validate_segment_structure() ◄─── DOMAIN LOGIC IN SCRIPTS        │
│  │                                                                       │
│  └─ install_trifecta_context.py                                         │
│     └─ Uses: validate_segment()                                         │
│                                                                          │
│  tests/                                                                  │
│  ├─ installer_test.py                                                   │
│  │  └─ sys.path.insert() workaround ◄─── HACK: Add scripts/ to path     │
│  │  └─ from install_FP import validate_segment_structure                │
│  │                                                                       │
│  src/                                                                    │
│  ├─ domain/          (pure logic, no dependencies)                       │
│  ├─ application/     (use cases)                                         │
│  ├─ infrastructure/  (CLI, I/O, templates)                              │
│  │  └─ file_system.py                                                   │
│  │     └─ Indexing: ALL .md files captured 2x ◄─── DUPLICATION BUG      │
│  │                                                                       │
│  _ctx/context_pack.json                                                 │
│  ├─ 7 chunks total                                                      │
│  ├─ skill.md appears 2x: skill + ref:skill.md                           │
│  └─ +1.7K wasted tokens (12% of pack)                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

PROBLEMS:
  ❌ validate_segment_structure() in scripts/ (should be in src/)
  ❌ Tests importing from scripts/ (non-standard Python)
  ❌ sys.path hack in test file
  ❌ Duplicate skill.md chunks in index
```

---

## Target Architecture (AFTER v1.1)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ DESIRED STRUCTURE (Clean Architecture Compliant)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  scripts/                                                                │
│  ├─ install_trifecta_context.py  [REFACTORED]                           │
│  │  └─ from src.infrastructure.validators import validate_segment      │
│  │                                                                       │
│  tests/                                                                  │
│  ├─ installer_test.py  [CLEAN]                                          │
│  │  └─ from src.infrastructure.validators import validate_segment_structure
│  │  └─ No sys.path hacks                                               │
│  │                                                                       │
│  src/                                                                    │
│  ├─ domain/          (pure logic)                                        │
│  ├─ application/     (use cases)                                         │
│  ├─ infrastructure/                                                      │
│  │  ├─ validators.py  [NEW] ✨                                          │
│  │  │  └─ validate_segment_structure() ◄─── MOVED HERE (proper location)
│  │  │  └─ ValidationResult (dataclass)                                  │
│  │  │                                                                    │
│  │  └─ file_system.py  [FIXED]                                          │
│  │     ├─ REFERENCE_EXCLUSION = {"skill.md"}                            │
│  │     └─ Skip ref-indexing for excluded files ◄─── DEDUPLICATION FIX   │
│  │                                                                       │
│  _ctx/context_pack.json  [OPTIMIZED]                                    │
│  ├─ 6 chunks total (was 7)                                              │
│  ├─ skill.md appears 1x only                                            │
│  └─ -1.7K tokens, cleaner index                                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

BENEFITS:
  ✅ Clean Architecture compliant
  ✅ Domain logic in proper layer
  ✅ Standard Python imports
  ✅ No test hacks
  ✅ Deduplication (-12% pack size)
```

---

## Implementation Workflow

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

### Phase 2: Update Imports (10 min)

```
scripts/install_trifecta_context.py:
  OLD: from install_FP import validate_segment
  NEW: from src.infrastructure.validators import validate_segment_structure
  
  Update function call:
    OLD: validate_segment(path)
    NEW: validate_segment_structure(path).valid
```

```
tests/installer_test.py:
  OLD: sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
       from install_FP import validate_segment_structure
  NEW: from src.infrastructure.validators import validate_segment_structure
```

### Phase 3: Fix Deduplication (10 min)

```
src/infrastructure/file_system.py:
  
  ADD at top level:
  ┌──────────────────────────────────────────────────────┐
  │ REFERENCE_EXCLUSION = {                              │
  │     "skill.md",         # Already indexed as primary  │
  │     "_ctx/session_*.md",  # Append-only, not indexed │
  │ }                                                    │
  └──────────────────────────────────────────────────────┘
  
  MODIFY in scan_files():
  ┌──────────────────────────────────────────────────────┐
  │ if file.name in REFERENCE_EXCLUSION:                 │
  │     continue  # Skip reference indexing              │
  └──────────────────────────────────────────────────────┘
```

### Phase 4: Validation & Testing (25 min)

```
1. Sync context pack:
   $ uv run trifecta ctx sync --segment .
   
   Expected: 6 chunks (was 7), -1.7K tokens, PASS validation

2. Run unit tests:
   $ uv run pytest tests/installer_test.py -v
   
   Expected: All PASS (imports now clean)

3. Type checking:
   $ uv run mypy src/ --strict
   
   Expected: All PASS (validators.py properly typed)

4. Linting:
   $ uv run ruff check .
   
   Expected: All PASS (clean imports, no sys.path hacks)

5. Context validation:
   $ uv run trifecta ctx validate --segment .
   
   Expected: PASS (no duplicates, all chunks valid)
```

---

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────┐
│ TASK DEPENDENCIES (Implementation Order)                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Task 1: Create validators.py                                           │
│  └─ No dependencies, can start immediately                              │
│                                                                          │
│  Task 2: Update install_trifecta_context.py                             │
│  └─ Depends on: Task 1 (validators.py must exist)                       │
│                                                                          │
│  Task 3: Update tests/installer_test.py                                 │
│  └─ Depends on: Task 1 (validators.py must exist)                       │
│                                                                          │
│  Task 4: Add exclusion list to file_system.py                           │
│  └─ No dependencies, can run in parallel with Tasks 2-3                 │
│                                                                          │
│  Task 5: Sync context pack                                              │
│  └─ Depends on: Task 4 (file_system.py must be updated)                 │
│                                                                          │
│  Task 6: Run gates (pytest, mypy, ruff)                                 │
│  └─ Depends on: Tasks 2-3 (imports must be updated)                     │
│                                                                          │
│  CRITICAL PATH: Task 1 → Task 2 → Task 3 → Task 6                       │
│  PARALLEL OPPORTUNITY: Task 4 can run during Tasks 2-3                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Success Criteria

| Criterion | Before | After | ✅ Check |
|-----------|--------|-------|---------|
| **Chunks in Pack** | 7 | 6 | `trifecta ctx validate` |
| **Wasted Tokens** | 1,770 | 0 | Diff output |
| **Skill.md Duplicates** | 2 | 1 | Index inspection |
| **Import Paths** | sys.path hack | src.infrastructure | grep sys.path |
| **Test Pass Rate** | 100% | 100% | pytest -v |
| **Type Safety** | mypy warnings | 0 warnings | mypy src/ |
| **Lint Issues** | 0 | 0 | ruff check |
| **Pack Validation** | PASS | PASS | trifecta ctx validate |

---

## Timeline

```
START: 2025-12-30 17:00 UTC
├─ Phase 1: Validator module            [15 min] ─┐
├─ Phase 2a: Update imports (scripts/)  [5  min] ─┼─ Can parallelize
├─ Phase 2b: Update imports (tests/)    [5  min] ─┤
├─ Phase 3: Fix deduplication           [10 min] ─┤
├─ Phase 4: Validation & testing        [25 min] ─┘
└─ END: ~17:55 UTC
   TOTAL: ~55 minutes
```

---

## Rollback Plan

If something breaks:
```
1. Revert validators.py creation
2. Revert imports in scripts/ and tests/
3. Revert file_system.py changes
4. Run: uv run trifecta ctx sync --segment .
5. Restore original state

Risk: LOW (changes are isolated, no data loss)
```

---

## Post-v1.1 Roadmap

```
v1.1 COMPLETE (After this sprint)
├─ Clean Architecture ✅
├─ Deduplication ✅
└─ Ready for v2.0

v2.0 (Q1 2026)
├─ Progressive Disclosure (AST/LSP)
├─ Semantic ranking (if still needed)
└─ Multi-language support

Note: Lexical search improvements deferred until after PD launch.
      Hypothesis: PD makes ranking/synonyms unnecessary.
```

---

**Plan Version**: 1.0  
**Status**: Ready for Implementation  
**Generated**: 2025-12-30 16:50 UTC  
**Confidence**: HIGH (low-risk, well-scoped changes)
