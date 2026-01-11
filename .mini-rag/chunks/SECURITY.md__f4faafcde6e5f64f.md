## Overview

Trifecta telemetry sanitizes absolute paths by default to prevent PII leaks.

**Default behavior**: Absolute paths in telemetry events are replaced with `<ABS_PATH_REDACTED>` or `<ABS_URI_REDACTED>`.

**Opt-in bypass**: Set `TRIFECTA_PII=allow` to preserve absolute paths for local debugging.

---
