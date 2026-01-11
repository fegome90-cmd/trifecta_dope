t`: Cache hits (file hash unchanged)
- `ast_cache_miss_count`: Cache misses (new parse required)

### LSP Counters
- `lsp_spawn_count`: Total LSP processes spawned
- `lsp_warming_count`: Processes in WARMING state
- `lsp_ready_count`: Processes that reached READY
- `lsp_failed_count`: Processes that failed (spawn/init error)
- `lsp_fallback_count`: Requests that fell back to AST-only

### File Read Counters
- `file_read_skeleton_bytes_total`: Bytes read in skeleton mode
- `file_read_excerpt_bytes_total`: Bytes read in excerpt mode
- `file_read_raw_bytes_total`: Bytes read in raw mode

---

## Summaries (in last_run.json)

```json
