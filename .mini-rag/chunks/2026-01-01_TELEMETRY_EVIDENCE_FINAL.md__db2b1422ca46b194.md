#### CLI Integration
**File:** [src/infrastructure/cli.py](src/infrastructure/cli.py)

**Entry points:**
- Line 173: `_get_telemetry()` initialization ✅ CONFIRMED
- Line 279: `ctx.search` calls `telemetry.observe()` ✅ CONFIRMED
- Line 317: `ctx.get` calls `telemetry.observe()` ✅ CONFIRMED
- Line 351: `ctx.validate` calls `telemetry.observe()` ✅ CONFIRMED
- Line 188+: `telemetry.flush()` on success ✅ CONFIRMED
- Line 203+: `telemetry.flush()` on error ✅ CONFIRMED
