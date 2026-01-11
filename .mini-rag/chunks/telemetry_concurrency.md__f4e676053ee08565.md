## Lossy by Design

**Philosophy:** Telemetry is for **observability and analytics**, not **transactional data**.

- **Acceptable:** 2-5% drop rate during burst writes (e.g., parallel test suite)
- **Unacceptable:** >10% drop rate (indicates pathological contention)
- **Monitoring:** `telemetry_drops` summary tracks drop rate in `last_run.json`

**Trade-offs:**
- ✅ **Zero latency cost:** No blocking waits, no retry loops
- ✅ **Zero deadlock risk:** Non-blocking locks cannot deadlock
- ✅ **Simplicity:** No complex queue/buffer/retry logic
- ❌ **Lossy:** Some events dropped under contention

---
