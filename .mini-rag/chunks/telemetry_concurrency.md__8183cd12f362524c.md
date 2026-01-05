## Migration Path (Future)

If drop rate becomes unacceptable (>10% sustained):

1. **Phase 1:** Add async queue (in-memory, bounded)
2. **Phase 2:** Background writer thread (drains queue to JSONL)
3. **Phase 3:** Graceful shutdown (flush queue before exit)

**Trigger:** User reports >10% drop rate in production workloads (not seen yet)

---
