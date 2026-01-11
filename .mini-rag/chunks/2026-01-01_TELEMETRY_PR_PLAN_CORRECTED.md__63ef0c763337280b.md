## PATCH NOTES (Cambios vs v1.0)

1. ✅ **Split into 2 PRs**: PR#1 (telemetry only), PR#2 (AST/LSP implementation)
2. ✅ **Reserved keys protection**: Fail-fast on collision with core fields
3. ✅ **LSP state machine**: COLD→WARMING→READY→FAILED (no aggressive timeouts)
4. ✅ **Path security**: `_relpath()` utility, enforce relative paths everywhere
5. ✅ **Concurrency model**: Declared lossy fcntl, no corruption acceptance in tests
6. ✅ **Event schema table**: Complete catalog with examples
7. ✅ **Remove speculative code**: PR#1 only scaffolding, no real parsers
8. ✅ **Test criteria fix**: Corruption-free validation, not exact counts
9. ✅ **Redaction policy**: Hash content, log sizes/ranges/relative paths only
10. ✅ **Dependencies**: PR#2 depends on PR#1 merge + tag
11. ✅ **DoD tightened**: No placeholders, all tests pass, mypy clean
12. ✅ **Timeline adjusted**: Clear handoff between phases

---
