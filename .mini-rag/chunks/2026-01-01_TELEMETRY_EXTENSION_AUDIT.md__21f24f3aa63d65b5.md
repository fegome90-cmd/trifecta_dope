### E.2 Integration Tests (Required)

**File:** `tests/integration/test_lsp_instrumentation.py` (NEW)

**Test cases:**

| Test | Objective | Assertion |
|------|-----------|-----------|
| `test_full_search_flow_logs_all_metrics` | Search emits all events | events.jsonl has ctx.search, file.read, bytes_read |
| `test_lsp_lifecycle_complete` | Full LSP flow | lsp.spawn → lsp.initialize → lsp.ready → lsp.definition |
| `test_fallback_on_lsp_timeout` | Timeout → fallback path | lsp.timeout event + lsp_fallback_count incremented |
| `test_concurrent_commands_no_corruption` | Lock mechanism works | spawn 3 commands, all events logged, no duplicates/drops |
| `test_summary_consistency` | last_run.json math correct | sum of counters == metrics.json, p50 < p95, etc. |

**Example test:**
