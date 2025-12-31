## CLI Usage Summary - 2025-12-31 (all recorded events)

**Commands**: 1056 total | Top: ctx.plan 92.6%, ctx.search 3.7%, ctx.sync 2.3%, ctx.get 0.7%
**Latency**: ctx.plan P50=11ms, P95=13ms (max 33ms); ctx.sync P50=2ms, P95=333ms (max 1191ms)
**Errors**: 4 failures | Top: status=error
**Key Insight**: ctx.search zero-hit rate is high (20/39 = 51.3%); biggest ROI is query coverage/precision.

### Search Effectiveness
- ctx.search hits: 47 total (avg ~1.2 hits/search)
- zero-hit searches: 20/39 (51.3%)

### Pack State (last run)
- pack_sha: 8b94080df77ba075
- stale_detected: false
- last_run_ts: 2025-12-31T18:12:16.970367+00:00
