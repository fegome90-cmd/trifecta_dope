### ✅ Telemetry Integration (Completed)
- [x] All events use PR#1 Telemetry.event(**extra_fields)
- [x] Extras go under `x` namespace (no reserved key collisions)
- [x] No absolute paths logged (only relative or hashed)
- [x] No content logged (only hashes, sizes, ranges)
- [x] Monotonic timing with perf_counter_ns → ms
