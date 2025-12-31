### 1. Fixed evaluate-plan Measurement

**File**: `src/infrastructure/cli.py`

- Added dataset identity tracking (SHA256, mtime, resolved path)
- Fixed hardcoded "40" → dynamic `{total}` in distribution header
- Split gate logic: Gate-NL vs Gate-L1 with different criteria
- Added proper outcome tracking (feature/alias/fallback mutually exclusive)
