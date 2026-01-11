### 🎯 TICKET 3: CLI + FileSystem (8 hours)
**Files:** `src/infrastructure/cli.py` + `src/infrastructure/file_system.py`

**Changes:**
1. cli.py line 279 (ctx.search):
   - Change `time.time()` → `time.perf_counter_ns()`
   - Add `bytes_read=file_system.total_bytes_read` to event()
   - Add `disclosure_mode=None` to event()

2. cli.py line 317 (ctx.get):
   - Same as search, but `disclosure_mode=mode`

3. file_system.py:
   - Add `self.total_bytes_read = 0` in `__init__()`
   - Track bytes per read: `self.total_bytes_read += len(content.encode())`
   - Increment counters: `telemetry.incr(f"file_read_{mode}_bytes_total", bytes_read)`

**Tests:**
- `test_cli_search_emits_bytes_read`
- `test_cli_get_emits_disclosure_mode`

**Verify:**
```bash
python -m pytest tests/unit/test_cli_instrumentation.py -v
python -m src.infrastructure.cli ctx search --segment . --query "test" --telemetry lite
# Check _ctx/telemetry/events.jsonl for bytes_read field
cat _ctx/telemetry/events.jsonl | jq '.[] | select(.cmd=="ctx.search") | {cmd, bytes_read}'
```
