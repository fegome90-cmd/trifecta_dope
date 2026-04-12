## Post-Drop Verification Report

**Agents:** 8 | **Passed:** 6 | **Failed:** 2 | **Timeout:** 0

✅ **syntax-src** — PASS (63ms)
  - Files checked: 119

✅ **syntax-tests** — PASS (135ms)
  - Files checked: 239

❌ **arch-deps** — FAIL (31ms)
  - Layers: {'domain': 21, 'application': 42, 'infrastructure': 33, 'platform': 8}

✅ **working-tree** — PASS (37ms)
  - Python files: 6/12 modified

✅ **cli-smoke** — PASS (709ms)

✅ **worktrees** — PASS (17ms)
  - Worktrees: 25

❌ **stale-refs** — FAIL (420ms)
  - Found 2 stale stash references in codebase
  - Stale refs: 2

✅ **unit-tests** — PASS (102899ms)
