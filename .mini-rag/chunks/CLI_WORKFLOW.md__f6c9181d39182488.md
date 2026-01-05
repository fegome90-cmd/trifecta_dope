## Telemetry Policy

**Default**: Telemetry enabled at `lite` level (`_ctx/telemetry/`)

**Environment Variables** (real):
- `TRIFECTA_NO_TELEMETRY=1`: Disable all telemetry
- `TRIFECTA_TELEMETRY_DIR=<path>`: Redirect telemetry output

**Per-command override** (where supported):
- `--telemetry off`: Disable for this invocation
- `--telemetry full`: Verbose telemetry
- `--telemetry lite`: Basic telemetry (default for most commands)

---
