# Security: PII in Telemetry

## Overview

Trifecta telemetry sanitizes absolute paths by default to prevent PII leaks.

**Default behavior**: Absolute paths in telemetry events are replaced with `<ABS_PATH_REDACTED>` or `<ABS_URI_REDACTED>`.

**Opt-in bypass**: Set `TRIFECTA_PII=allow` to preserve absolute paths for local debugging.

---

## PII Patterns Redacted

The following patterns are automatically sanitized in telemetry events:

- **Posix absolute paths**: `/Users/`, `/home/`, `/private/var/`
- **Windows paths**: `C:\Users\`, `D:\Users\`
- **WSL paths**: `/mnt/c/Users/`, `/mnt/C/Users/`
- **File URIs**: `file://`

---

## Cleaning Legacy Telemetry

If you have PII in existing `_ctx/telemetry/events.jsonl` from before sanitization was implemented:

### Option 1: Delete (Simple)

```bash
rm ./_ctx/telemetry/events.jsonl
```

The file will be recreated automatically on the next telemetry event.

### Option 2: Scrub (Preserve History)

```bash
python scripts/scrub_telemetry_pii.py ./_ctx/telemetry/events.jsonl
```

This rewrites the file with PII patterns replaced by `<ABS_PATH_REDACTED>`.

**Backup**: The scrubber creates a `.bak` backup before modifying the file.

---

## Verification

Check for PII in telemetry:

```bash
# Search for common PII patterns
rg "/Users/|/home/|/private/var/|file://|C:\\Users\\" ./_ctx/telemetry/events.jsonl

# If output is empty, telemetry is clean
```

---

## Related

- Implementation: `src/infrastructure/telemetry.py`
- Tests: `tests/unit/test_telemetry_pii_sanitizer.py`
- Acceptance tripwire: `tests/acceptance/test_telemetry_no_pii_in_events.py`
