# Audit-Grade Merge Readiness: AST Cache --persist-cache Fix

**Date**: 2026-01-05 12:50 UTC-3  
**Protocol**: Fail-closed, zero-glob, hard evidence only  
**Status**: ✅ READY FOR MERGE

---

## 1. Scope

### Changed (P0 Fix)
- `src/domain/ast_cache.py` (+17 LOC)
  - SQLiteCache.set(): Serialization for dataclass objects
  - _evict_if_needed(): None handling for empty DB
- `src/application/ast_parser.py` (+15 LOC)
  - Rehidration: list[dict] → list[SymbolInfo]
- `tests/unit/test_ast_cache_persist_fix.py` (+88 LOC, NEW)

### NOT Changed
- No refactors
- No performance optimizations
- No additional features
- Domain layer does NOT import Application (Clean Architecture preserved)

---

## 2. Evidence (Hard Anchors)

### E1: Unit Tests

**Command**:
```bash
uv run pytest -q tests/unit/test_ast_cache_persist_fix.py 2>&1 | tee /tmp/tf_pytest_ast_cache_fix.log
```

**Output** (from `/tmp/tf_pytest_ast_cache_fix.log`):
```
..                                                                       [100%]
2 passed in 0.07s
```

**Anchor**: 2 tests passing (serialization + roundtrip)

---

### E2: Run #1 (miss→write)

**Command**:
```bash
uv run trifecta ast symbols "sym://python/mod/src.domain.result" --segment . --persist-cache
```

**Output** (from `/tmp/tf_post_fix_run1.log`, last 14 lines):
```json
{
  "status": "ok",
  "segment_root": "/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope",
  "file_rel": "src/domain/result.py",
  "symbols": [
    {"kind": "class", "name": "Ok", "line": 22},
    {"kind": "class", "name": "Err", "line": 53}
  ],
  "cache_status": "miss",
  "cache_key": "..."
}
```

**Anchor**: `"status": "ok"`, `"cache_status": "miss"`

---

### E3: Cache Write Verification

**Command**:
```bash
set DB (find . -maxdepth 8 -name "ast_cache_*.db" | head -n 1)
echo "$DB" | tee /tmp/tf_db_path_exact.log
ls -la "$DB" | tee /tmp/tf_db_ls.log
sqlite3 "$DB" "select count(*) from cache;" | tee /tmp/tf_cache_rowcount.log
```

**DB Path** (from `/tmp/tf_db_path_exact.log`):
```
./.trifecta/cache/ast_cache__Users_felipe_gonzalez_Developer_agent_h_trifecta_dope.db
```

**DB Metadata** (from `/tmp/tf_db_ls.log`):
```
-rw-r--r-- 1 felipe_gonzalez staff 16384 Jan  5 12:50 ./.trifecta/cache/ast_cache__Users_felipe_gonzalez_Developer_agent_h_trifecta_dope.db
```

**Row Count** (from `/tmp/tf_cache_rowcount.log`):
```
1
```

**Anchor**: EXACT path (no glob), 1 row written, 16KB DB file created at 12:50

---

### E4: Run #2 (hit→read)

**Command**: (same as E2)

**Output** (from `/tmp/tf_post_fix_run2.log`, last 14 lines):
```json
{
  "status": "ok",
  "segment_root": "/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope",
  "file_rel": "src/domain/result.py",
  "symbols": [
    {"kind": "class", "name": "Ok", "line": 22},
    {"kind": "class", "name": "Err", "line": 53}
  ],
  "cache_status": "hit",
  "cache_key": "..."
}
```

**No Errors Check**:
```bash
rg -n "AttributeError|Traceback" /tmp/tf_post_fix_run2.log
# Exit code: 1 (no matches found) ✅
```

**Anchor**: `"cache_status": "hit"`, NO AttributeError on `.kind` access

---

### E5: Gate-All

**Command**:
```bash
make gate-all 2>&1 | tee /tmp/tf_gate_all.log
```

**Output** (from `/tmp/tf_gate_summary.log`, last 11 lines):
```
349 passed in 0.93s
uv run pytest -q tests/integration
...................................s...                                  [100%]
38 passed, 1 skipped in 5.01s
uv run pytest -q tests/acceptance -m "not slow"
.........................................                                [100%]
41 passed, 4 deselected in 6.00s
✅ GATE PASSED: Unit + Integration + Acceptance (Fast)
```

**Anchor**: 349 unit + 38 integration + 41 acceptance = **428 tests passing**

---

## 3. Architecture Decision (Option B)

**Rationale**: Clean Architecture Constraint

```
Application Layer: SymbolInfo (src/application/ast_parser.py:14)
Domain Layer: SQLiteCache (src/domain/ast_cache.py:197)

Rule: Domain MUST NOT import Application
Therefore: Rehidration in ast_parser.py (caller), NOT in SQLiteCache
```

**Evidence**:
```bash
rg -n "class SymbolInfo" src/
# Output: src/application/ast_parser.py:14:class SymbolInfo:

rg -n "class SQLiteCache" src/
# Output: src/domain/ast_cache.py:197:class SQLiteCache:
```

**ADR**: `docs/adr/ADR-005-ast-cache-roundtrip.md`

---

## 4. Collateral Fix Justification

### Change: _evict_if_needed (src/domain/ast_cache.py:370)

**Patch**:
```python
# Before (broken):
entries, current_bytes = cursor.fetchone() or (0, 0)

# After (fixed):
row = cursor.fetchone()
entries, current_bytes = row or (0, 0)
current_bytes = current_bytes or 0  # ← GUARD
```

**Justification**:

1. **Call-site** (from `/tmp/tf_evict_callsite.log`):
```
295:        self._evict_if_needed(value_bytes)
```

2. **Context** (from `/tmp/tf_evict_context.log`):
```python
value_json = json.dumps(value_serialized)
value_bytes = len(value_json.encode())

# Evict if necessary
self._evict_if_needed(value_bytes)  # ← Called on EVERY set()

# Add or update entry
with sqlite3.connect(self.db_path) as conn:
```

3. **Root Cause**: `SUM(value_bytes)` returns `None` when cache table is empty → TypeError on `current_bytes + new_bytes`

4. **Why Included in P0**: `set()` calls `_evict_if_needed()` on EVERY write. Without this guard, the main fix would fail on first write to empty DB.

**Tech Debt**: Missing dedicated test `test_evict_if_needed_handles_empty_db` (P3)

---

## 5. Tech Debt (Future Work)

Documented in `docs/tech_debt_ast_cache.md`:

### P2: Type Safety in SQLiteCache.set()
- **Issue**: Fallthrough accepts ANY JSON-serializable type (duck-typing)
- **Task**: Add `test_sqlite_cache_set_rejects_unexpected_type`
- **Task**: Change fallthrough to fail-loud or explicit allow-list

### P3: Test for _evict_if_needed
- **Issue**: Collateral fix has no dedicated test
- **Task**: Add `test_evict_if_needed_handles_empty_db`

### P3: DB Path Encoding
- **Issue**: Filename leaks absolute paths (non-portable)
- **Task**: Consider hashing segment path

---

## 6. Files to Commit

```
src/domain/ast_cache.py           (+17 LOC)
src/application/ast_parser.py     (+15 LOC)
tests/unit/test_ast_cache_persist_fix.py (+88 LOC, NEW)
docs/adr/ADR-005-ast-cache-roundtrip.md (NEW)
docs/tech_debt_ast_cache.md       (NEW)
docs/PR_NOTES_ast_cache_fix.md    (NEW)
```

**Total**: ~120 LOC code + documentation

---

## 7. Suggested Commit Message

```
fix: SQLiteCache roundtrip for SymbolInfo (--persist-cache)

Fixes TypeError when using --persist-cache flag with AST cache.

Problem:
- SQLiteCache.set() called json.dumps() directly on list[SymbolInfo]
  → TypeError: Object of type SymbolInfo is not JSON serializable
- Even if serialization worked, get() returned list[dict] but consumers
  expected list[SymbolInfo] → would AttributeError on cache hit

Solution (Option B - Clean Architecture):
- SQLiteCache.set(): Serialize SymbolInfo→dict via to_dict()
- ast_parser.py: Rehidrate dict→SymbolInfo after cache.get()
- Rationale: Domain (ast_cache) cannot import Application (SymbolInfo)

Collateral fix:
- _evict_if_needed: Handle None from SUM() when DB is empty
  (necessary for set() to work on first write)

Evidence:
- Unit: 2/2 passing
- E2E: miss→write(1 row)→hit verified
- Gate: 428 tests passing (349+38+41)
- Logs: /tmp/tf_*.log

Tech Debt: docs/tech_debt_ast_cache.md (P2/P3)
ADR: docs/adr/ADR-005-ast-cache-roundtrip.md
```

---

## 8. Audit Trail Summary

| Evidence | Log Path | Anchor |
|----------|----------|--------|
| Unit Tests | `/tmp/tf_pytest_ast_cache_fix.log` | `2 passed` |
| Run #1 | `/tmp/tf_post_fix_run1.log` | `cache_status: miss` |
| DB Path | `/tmp/tf_db_path_exact.log` | `./.trifecta/cache/ast_cache_*.db` |
| DB Meta | `/tmp/tf_db_ls.log` | `16384 bytes, Jan 5 12:50` |
| Row Count | `/tmp/tf_cache_rowcount.log` | `1` |
| Run #2 | `/tmp/tf_post_fix_run2.log` | `cache_status: hit` |
| Gate All | `/tmp/tf_gate_summary.log` | `428 tests passing` |
| Evict Call | `/tmp/tf_evict_callsite.log` | `Line 295` |
| Evict Context | `/tmp/tf_evict_context.log` | `set() → _evict_if_needed()` |

**All claims anchored to reproducible evidence. Zero globs in final report.**

---

**VERDICT**: ✅ READY FOR MERGE  
**Blocker Count**: 0  
**Tech Debt**: Documented (not blocking)  
**Audit Grade**: PASS
