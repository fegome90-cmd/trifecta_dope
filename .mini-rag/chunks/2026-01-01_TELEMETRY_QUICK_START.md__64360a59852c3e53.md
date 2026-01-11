## CRITICAL RULES (REMEMBER!)

1. **Monotonic timing:** Always use `time.perf_counter_ns()` for relative durations
   ```python
   start_ns = time.perf_counter_ns()
   # ... operation ...
   elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)
   ```

2. **Relative paths only:** No absolute paths in telemetry
   ```python
   # WRONG:
   telemetry.event("ast.parse", {"file": "/Users/alice/my_code.py"}, ...)

   # RIGHT:
   telemetry.event("ast.parse", {"file": "src/domain/models.py"}, ...)
   ```

3. **Extended fields in `event()`:** Merge kwargs into JSON payload
   ```python
   telemetry.event(
       "ctx.search",
       {"query": "test"},
       {"hits": 2},
       145,  # timing_ms
       bytes_read=1024,       # NEW
       disclosure_mode="skeleton",  # NEW
   )
   ```

4. **LSP READY definition:** Initialize + (diagnostics OR definition success)
   ```
   lsp.spawn → lsp.initialize → [lsp.ready]
                                   (when publishDiagnostics received OR first definition_response)
   ```

---
