---
title: "Trifecta MVP: Immediate Action Plan"
date: 2025-12-30
scope: Script Refactor + Deduplication
roadmap_alignment: v1.1 (not RAG improvement)
---

# Action Plan: Script Refactor + Deduplication

**Context**: Trifecta MVP evaluation revealed 2 quick wins:
1. Duplicate `skill.md` chunks (+1.7K wasted tokens)
2. `install_FP.py` in scripts/ needs integration with domain layer

**Constraint**: RAG improvements (ranking, synonym expansion) are deprioritized.  
**Future Focus**: Progressive Disclosure (AST/LSP) is the next major milestone.

---

## Issue #1: Duplicate skill.md Chunks

### Current State
```
Index Entry 1: skill:773705da1d (doc='skill')          [885 tokens]
Index Entry 2: ref:skill.md:ce2488eaa2 (doc='ref:skill')  [885 tokens]
Total Waste:   +1,770 tokens (12% of pack)
```

### Root Cause
Two indexing rules are capturing the same file:
1. **Primary rule**: Index `skill.md` as doc type `skill`
2. **Fallback rule**: Index all `.md` as references (`ref:<filename>`)

### Solution (Minimal)

**Option A: Exclude rule (Simplest)**
- Add `skill.md` to exclusion list for reference indexing
- Keep primary `skill` chunk only
- Impact: -1.7K tokens, cleaner index

```python
# src/infrastructure/file_system.py

REFERENCE_EXCLUSION = {
    "skill.md",  # Already indexed as primary 'skill' doc
    "_ctx/session_*.md",  # Session is append-only, not indexed as ref
}

# In scan_files():
if file.name in REFERENCE_EXCLUSION:
    continue  # Skip reference indexing
```

**Option B: Merge rule (Better)**
- Detect duplicate content (SHA256)
- Keep highest-priority version (skill > ref)
- Impact: Same as A, but handles future duplicates

**Recommendation**: **Option A** (MVP scope, less code).

### Implementation
1. Edit [src/infrastructure/file_system.py](src/infrastructure/file_system.py) → Add exclusion list
2. Run `uv run trifecta ctx sync --segment .`
3. Verify: `uv run trifecta ctx validate --segment .` → Should show -1 chunk, same content

---

## Issue #2: install_FP.py Script Integration [✅ COMPLETED]

**Status**: install_FP.py is now the stable installer script.
- Uses Clean Architecture imports from src/infrastructure/validators
- install_trifecta_context.py marked as DEPRECATED

---

## Original Analysis:

### Current State
```
scripts/install_FP.py              [122 lines, pure Python]
  └─ validate_segment_structure()  [Pure domain logic]
      └─ Used by: tests/installer_test.py

tests/installer_test.py            [56 lines]
  └─ Imports from scripts/ (non-standard)
  └─ Added workaround: sys.path.insert() + pyproject.toml pythonpath
```

### Problem
- `install_FP.py` is a **script**, but contains **domain logic**
- Should live in `src/domain/` or `src/application/`
- Clean Architecture violation (scripts shouldn't contain reusable logic)

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

## Implementation Sequence

| # | Task | File | Time | Priority |
|---|------|------|------|----------|
| 1 | Move validator to src/infrastructure/ | validators.py | 15m | HIGH |
| 2 | Update install_trifecta_context.py | scripts/ | 10m | HIGH |
| 3 | Update test imports | tests/installer_test.py | 5m | HIGH |
| 4 | Add exclusion list for skill.md | file_system.py | 10m | HIGH |
| 5 | Sync + validate context pack | _ctx/ | 5m | HIGH |
| 6 | Run gates (pytest, mypy, ruff) | tests/ | 10m | HIGH |

**Total**: ~55 minutes

---

## Why NOT Major RAG Improvements?

### Current Issues (MVP Evaluation)
1. Primitive ranking (0.50 for all)
2. No synonym expansion
3. Large documents not fragmented

### Why Defer?

**Reason 1: Limited ROI for Segment-Local Search**
- Trifecta is segment-local, not global
- Segments are small (~7K tokens for trifecta_dope)
- Lexical search "good enough" for small sets

**Reason 2: Progressive Disclosure Changes Everything**
- v2 roadmap: AST-based context (code symbols, not docs)
- LSP integration (IDE-native context)
- Both make lexical search irrelevant

**Reason 3: MVP is Already Operational**
- 99.9% token precision
- <5s per cycle
- 100% budget compliance
- No critical issues

### Better Use of Time
- ✅ Clean Architecture (move script logic)
- ✅ Deduplication (quick win, -12% pack size)
- ✅ Prepare for Progressive Disclosure (AST hooks)
- ✅ Real-world testing (larger segments)

**After v1.1 release**, evaluate if ranking is still needed.  
Hypothesis: Progressive Disclosure makes it unnecessary.

---

## Roadmap Alignment

```
TRIFECTA TIMELINE
═════════════════════════════════════════════════════════════════

v1.0 (Current - MVP)
├─ Build context pack from markdown
├─ Lexical search (simple, deterministic)
├─ Budget-aware retrieval
└─ Session logging (append-only)

v1.1 (This Sprint)
├─ Clean Architecture (scripts → src/)
├─ Deduplication (skip duplicate chunks)
├─ Fragment large documents (H2 headers)
└─ Fail-closed validation (stale detection)

v2.0 (Q1 2026 - Progressive Disclosure)
├─ AST-based context (symbol extraction)
├─ LSP integration (IDE-native)
├─ Semantic ranking (TBD: embeddings or rule-based)
└─ Multi-language support (Python, TypeScript, etc.)

v2.1+
└─ (RAG improvements only if needed after PD launch)
```

---

## Session Checkpoint

**Current Status**:
- ✅ MVP evaluation complete (report generated)
- ✅ 2 quick wins identified (script refactor, deduplication)
- ✅ Roadmap aligned (RAG deferred to post-PD)
- ⏳ Ready for implementation (v1.1 tasks)

**Next Action**:
1. Implement script refactor (Option A)
2. Add exclusion list for deduplication
3. Run gates
4. Tag as v1.1-rc1

---

**Plan Generated**: 2025-12-30 16:50 UTC  
**Alignment**: v1.1 sprint, not RAG improvements  
**Scope**: Clean Architecture + Deduplication  
**Confidence**: HIGH (low-risk, high-value changes)
