### E.1 Unit Tests (Required)

**File:** `tests/unit/test_telemetry_ast_lsp.py` (NEW)

**Test cases:**

| Test | Objective | Assertion |
|------|-----------|-----------|
| `test_ast_event_uses_monotonic_clock` | Verify perf_counter_ns used | `timing_ms > 0`, no backwards jumps |
| `test_ast_event_redacts_absolute_path` | No /Users/.../ in logs | Relative path only in event |
| `test_lsp_ready_event_fires_on_diagnostics` | READY trigger correct | `cmd == "lsp.ready"` when publishDiagnostics received |
| `test_lsp_timeout_falls_back_to_tree_sitter` | Fallback on 500ms exceed | `lsp_timeout_count` incremented, result is fallback |
| `test_bytes_read_per_command_aggregated` | Bytes tracked per mode | `file_read_skeleton_bytes_total` in metrics.json |
| `test_event_extra_fields_serialized` | Extended fields in payload | `bytes_read`, `disclosure_mode` in events.jsonl |
| `test_no_lock_skip_on_critical_events` | Critical events don't drop | LSP ready, command start/end logged even if lock busy |
| `test_summary_calculates_p50_p95_correctly` | Aggregation math | Given dataset, p50 == median, p95 == 95th percentile |

**Example test:**
