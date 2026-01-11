### Recommendations

1. **APPROVED FOR IMPLEMENTATION:** Begin with Ticket 1 (Telemetry extension)
2. **SEQUENCE:** T1 → T2 → T3 → T4 (do not parallelize; each depends on previous)
3. **TIMELINE:** 4–5 consecutive days, 1 developer
4. **RESOURCE:** Assign senior engineer (familiar with async, file I/O, JSON-RPC)
5. **DEPENDENCY:** `pip install tree-sitter tree-sitter-python` before T2
6. **TESTING:** Run full suite nightly; target >80% coverage
7. **DEPLOYMENT:** Merge all 4 PRs to main; tag release; monitor drop_skipped warnings
