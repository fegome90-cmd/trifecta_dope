### N.1 Lock Skipping (Acceptable Risk)

The POSIX fcntl non-blocking lock is **lossy by design** (skip write if busy). This is **acceptable for telemetry** because:
1. **Not critical data**: Telemetry is best-effort observability, not transactional.
2. **Fail-safe**: Never corrupts events.jsonl; just drops the entire event.
3. **Measurable**: Drop count recorded in `telemetry_lock_skipped` warnings.

**However:** For MVP, ensure critical events (lsp.ready, command.end) use the **existing event() mechanism** (same lock as everything else) to maintain single failure mode.
