#### Changes

**File:** `src/infrastructure/telemetry.py`

**After line 15 (before class Telemetry), add:**

```python
# Reserved keys that cannot be overridden by extra_fields
RESERVED_KEYS = frozenset({
    "ts", "run_id", "segment", "cmd", "args", "result",
    "timing_ms", "tokens", "warnings"
})

def _relpath(root: Path, target: Path) -> str:
    """
    Convert absolute path to relative path for telemetry.
    Prevents logging absolute paths or URIs with user/system info.

    Args:
        root: Repository/segment root (workspace root)
        target: File path to convert

    Returns:
        Relative path string, or external/<hash8>-<name> if outside root

    Example:
        >>> _relpath(Path("/workspaces/repo"), Path("/workspaces/repo/src/app.py"))
        'src/app.py'
        >>> _relpath(Path("/workspaces/repo"), Path("/usr/lib/python3.12/typing.py"))
        'external/a3b4c5d6-typing.py'  # hash ensures uniqueness without exposing path
    """
    try:
        return str(target.relative_to(root))
    except ValueError:
        # File outside workspace: hash path for privacy + uniqueness
        import hashlib
        path_hash = hashlib.sha256(str(target).encode()).hexdigest()[:8]
        return f"external/{path_hash}-{target.name}"
```

**Line 113: Modify `event()` signature:**
