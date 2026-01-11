# Clean Boot Reproducibility v1 — WO-0007

**Created**: 2026-01-05T22:59:00-03:00  
**SHA**: (verified_at_sha will be added post-validation)

---

## Objective

Validate that Trifecta's `ctx sync → ctx search` pipeline is **reproducible in clean worktree** without pre-existing state.

**NO magic**:
- No pre-generated `context_pack.json`
- No pre-existing `AGENTS.md`, `prime_*.md`, `agent_*.md`, `session_*.md`
- Real pipeline only: `ctx sync` creates pack, `ctx search` uses it

---

## Why NOT Use Pre-Generated Pack?

**Problem**: Previous tests relied on `_ctx/context_pack.json` already existing in repo state.

**Impact**: Clean worktree boot failed with "Context pack not found" error.

**Solution**: Test must generate pack from scratch via `ctx sync`, then validate `ctx search` works.

---

## Test Design

### Mini-Repo Fixture

**Location**: `tests/integration/test_repro_clean_sync_then_search.py`

**Fixture creates**:
```
tmp_path/mini_repo/
├── docs/servicio.md         # Contains: "SERVICIO_ANCHOR_TOKEN"
├── README.md                 # Noise
├── configs/
│   ├── anchors.yaml          # Minimal: "servicio" as weak anchor
│   └── aliases.yaml          # Alias: "servicio" → "servicio.md"
```

**No** `_ctx/` or `AGENTS.md` pre-created. Pipeline generates them.

---

## Pipeline Flow

```
1. ctx sync --segment mini_repo
   → Creates _ctx/context_pack.json

2. ctx search --segment mini_repo --query "servicio" --limit 5
   → Reads pack, returns chunks
```

---

## A/B Linter Validation

**Test**: `test_ctx_search_ab_linter_off_zero_on_nonzero`

**Query**: `"servicio"` (vague, 1 token)

**Expected**:
- **OFF** (`--no-lint`): 0 hits (no expansion)
- **ON** (`TRIFECTA_LINT=1`): >0 hits (expands to `servicio.md`)

**Assertion**:
```python
ids_off = parse_chunk_ids(result_off.stdout)
ids_on = parse_chunk_ids(result_on.stdout)

assert len(ids_off) == 0, "OFF should return 0 hits"
assert len(ids_on) > 0, "ON should return >0 hits"
```

---

## Gate Script

**Location**: `scripts/gate_clean_worktree_repro.sh`

**Execution**:
```bash
1. git worktree add /tmp/tf_repro_gate_<SHA> HEAD
2. cd /tmp/tf_repro_gate_<SHA>
3. rm -rf _ctx  # Remove any state
4. uv run pytest -xvs tests/integration/test_repro_clean_sync_then_search.py
5. Exit 0 if pass, Exit 1 if fail
6. Cleanup worktree
```

**CI-Ready**: No interactive prompts, deterministic exit codes.

---

## Expected Output

### ctx sync
```
✓ Context built for segment: mini_repo
  Digest: <hash>
  Chunks: 3
  Index entries: 3
```

### ctx search (OFF)
```
❌ Search Results (0 hits)
```

### ctx search (ON)
```
✓ Search Results (2 hits)
  1. prime:<digest>:chunk-0
  2. prime:<digest>:chunk-1
```

---

## Success Criteria

- ✅ `ctx sync` creates `_ctx/context_pack.json` from scratch
- ✅ `ctx search` returns results without "Context pack not found" error
- ✅ A/B linter: OFF=0, ON>0
- ✅ Gate passes in clean worktree

---

## Failure Modes

| Failure | Root Cause | Fix |
|---------|------------|-----|
| "Context pack not found" after sync | `ctx sync` didn't create pack | Check sync logic, validate pack path |
| OFF>0 hits | Linter not disabled with `--no-lint` | Verify flag handling in CLI |
| ON=0 hits | Linter config missing or broken | Check `anchors.yaml`, `aliases.yaml` in fixture |
| Gate fails in worktree | Hidden dependency on main repo state | Identify and remove dependency |

---

## Commands for Manual Validation

```bash
# Run test locally
uv run pytest -xvs tests/integration/test_repro_clean_sync_then_search.py

# Run gate script
bash scripts/gate_clean_worktree_repro.sh
```

---

**END OF REPORT**
