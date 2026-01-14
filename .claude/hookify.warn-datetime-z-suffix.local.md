---
name: warn-datetime-z-suffix
enabled: true
event: file
action: warn
pattern: (fromisoformat\([^)]*['"][^'"]*Z['"]|datetime\.strptime\([^)]*%Z[^)]*\))
---

⚠️ **Datetime 'Z' Suffix Parsing Issue Detected**

You're using datetime parsing methods that don't handle the 'Z' UTC suffix correctly.

**Problem 1: `datetime.fromisoformat()` with 'Z'**
```python
# ❌ This will raise ValueError
datetime.fromisoformat("2025-01-14T10:30:00Z")

# ✅ Replace 'Z' with '+00:00' first
datetime.fromisoformat("2025-01-14T10:30:00Z".replace('Z', '+00:00'))

# ✅ Or use a helper function
def parse_datetime_iso(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
```

**Problem 2: `strptime()` with `%Z` on macOS**
```python
# ❌ Unreliable on macOS (platform-dependent)
datetime.strptime("2025-01-14T10:30:00Z", "%Y-%m-%dT%H:%M:%SZ")

# ✅ Use strptime with explicit timezone
from datetime import timezone, datetime
datetime.strptime("2025-01-14T10:30:00", "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)

# ✅ Or use dateutil.parser (if available)
from dateutil import parser
parser.isoparse("2025-01-14T10:30:00Z")
```

**Code review reference:** CRITICAL-1 from code-reviewer agent - datetime fields passed as strings to WorkOrder entity will cause runtime type errors.

**Best practice:**
```python
from datetime import datetime, timezone

def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 datetime string, handling 'Z' suffix."""
    if value is None:
        return None
    # Replace Z with +00:00 for fromisoformat compatibility
    iso_value = value.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(iso_value)
    except ValueError:
        raise ValueError(f"Invalid datetime format: '{value}'. Expected ISO 8601 format.")
```

**Impact:** Without proper parsing, datetime comparisons like `finished_at < started_at` will fail or produce incorrect results.
