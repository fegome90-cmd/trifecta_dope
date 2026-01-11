### ❌ What IS NOT Guaranteed

1. **Event Count Exactness:** Under lock contention, some events dropped (2-5% typical)
2. **Event Ordering:** Events from concurrent processes may appear out-of-order
3. **Write Blocking:** Writers NEVER wait for locks - they skip and continue
4. **Drop Notification:** Dropped events not logged individually (only aggregate stats)

---
