## Summary

- **Model:** Lossy, non-blocking POSIX file locking
- **Guarantees:** No corruption, atomic appends
- **Trade-off:** Accept 2-5% drops for zero latency cost
- **Monitoring:** Drop rate tracked in `telemetry_drops` summary
- **Usage:** Safe for analytics, unsafe for billing/compliance
- **Testing:** Verify no corruption, accept lossy counts
