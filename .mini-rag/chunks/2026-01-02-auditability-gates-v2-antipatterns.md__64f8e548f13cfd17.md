**DoD:**
- [ ] Unit test `test_sanitized_dump_removes_absolute_paths` pasa
- [ ] Integration test `test_ctx_sync_produces_no_pii` pasa
- [ ] CWD test `test_ctx_sync_from_different_cwd` pasa
- [ ] Manual gate: `uv run trifecta ctx sync -s . && rg -n '"/Users/' _ctx/context_pack.json; echo "RC=$?" (1=PASS)`
- [ ] Commit: "fix(g2): sanitize paths in context_pack.json (AP6, AP7, AP8)"

---
