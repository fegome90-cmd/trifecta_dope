# Known Test Failures

> This document tracks pre-existing test failures that are NOT regressions.

## test_e2e_evidence_stop_real_cli

**File**: `tests/acceptance/test_pd_evidence_stop_e2e.py`
**Status**: PRE-EXISTING (not a regression)

### Evidence

| Metric | Value |
|--------|-------|
| HEAD commit | 51b7bf3 |
| Test added | a5ff2f0 (2026-01-04) |
| First linter commit | 672a2b8 |

### Root Cause

The test searches for "ContextService" but this term **does not exist** in the segment's context_pack.json:

```bash
$ uv run trifecta ctx search --segment . --query "ContextService" --limit 3
No results found for query: 'ContextService'
```

### Logs

- `_ctx/logs/gate_fail_head.log`

### Gate Alternative

Until the context_pack.json is regenerated with documentation containing "ContextService", use:

```bash
uv run pytest -q --ignore=tests/acceptance/test_pd_evidence_stop_e2e.py
```

### Resolution Path

1. Add documentation mentioning "ContextService" to segment (e.g., update agent.md)
2. Regenerate context_pack.json: `trifecta ctx sync --segment .`
3. Verify search returns hits: `trifecta ctx search -s . -q "ContextService"`
4. Remove from KNOWN_FAILS.md

---

**Generated**: 2026-01-05 18:10 UTC
