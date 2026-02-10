# Design: Fix Code Review Findings for telemetry_rotate.py

**Date:** 2026-02-10
**Epic:** E-0012 (AST Cache Operability)
**Related:** WO-0018C (Documentation & Telemetry Cleanup)
**Status:** Design Complete

---

## Overview

This design addresses CRITICAL, HIGH, and MEDIUM issues found in the code review of `scripts/telemetry_rotate.py` (WO-0018C). The fixes follow TDD methodology: write failing tests first (RED), implement fixes (GREEN), then refactor (IMPROVE).

---

## Architecture

### Test Structure

Create `tests/unit/test_telemetry_rotate.py` following the pattern from `test_scrub_telemetry_pii.py`:

```python
tests/unit/test_telemetry_rotate.py
├── TestGetTelemetryDir      # Env var resolution
├── TestCountEvents           # File reading, edge cases
├── TestGetSizeMb             # Size calculation
├── TestRotateEvents          # Core rotation logic
└── TestRotateEventsErrors    # Error conditions
```

### Separation of Concerns

Introduce `RotationResult` dataclass (frozen) to return structured data instead of using `print()`:

```python
@dataclass(frozen=True)
class RotationResult:
    from_path: Path
    to_path: Path
    size_mb: float
    event_count: int
```

The CLI layer (`main()`) handles formatting and user output.

---

## Error Handling Strategy

### Result Types

Wrap all file I/O operations using `Result[T, str]` from `src/domain/result.py`:

```python
from src.domain.result import Ok, Err, Result

def count_events(events_file: Path) -> Result[int, str]:
    """Count newline-delimited JSON events."""
    if not events_file.exists():
        return Ok(0)

    try:
        count = 0
        with open(events_file, "r", encoding="utf-8") as f:
            for _ in f:
                count += 1
        return Ok(count)
    except PermissionError:
        return Err(f"Permission denied reading {events_file}")
    except UnicodeDecodeError:
        return Err(f"File encoding error in {events_file} (expected UTF-8)")
    except OSError as e:
        return Err(f"OS error reading {events_file}: {e}")
```

### Exception Hierarchy

| Exception | Error Message |
|-----------|---------------|
| `PermissionError` | "Permission denied accessing {path}" |
| `UnicodeDecodeError` | "File encoding error in {path} (expected UTF-8)" |
| `FileExistsError` | "Target file already exists: {path}" |
| `OSError` | "OS error: {details}" |

### main() Error Handling

```python
def main() -> int:
    args = parse_args()

    result = rotate_events(events_file)

    if isinstance(result, Err):
        print(f"Error: {result.value}", file=sys.stderr)
        return 1

    # Ok case - format and print
    print(f"Rotated: {result.value.from_path} -> {result.value.to_path}")
    return 0
```

---

## Path Resolution & Configuration

### repo_root() Function

Add to `scripts/paths.py` (or use existing):

```python
def repo_root() -> Path:
    """Find repository root by searching for pyproject.toml upwards."""
    current = Path(__file__).resolve().parent
    for _ in range(5):
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Repository root not found")
```

Update `telemetry_rotate.py`:
```python
from scripts.paths import repo_root

def get_telemetry_dir() -> Path:
    if env_dir := os.environ.get("TRIFECTA_TELEMETRY_DIR"):
        return Path(env_dir)
    return repo_root() / "_ctx" / "telemetry"
```

### CLI Arguments

Replace `sys.argv` parsing with `argparse`:

```python
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rotate Trifecta telemetry files")
    parser.add_argument("--force", action="store_true", help="Skip confirmation")
    return parser.parse_args()
```

---

## Testing Strategy (TDD)

### Test Execution Order

1. **RED** - Write failing test
2. **GREEN** - Fix code to pass
3. **VERIFY** - Run `ruff format`, `mypy`, `pytest`
4. **COMMIT**
5. Repeat

### Test Categories

#### 1. Boundary Tests
- Exactly at thresholds: `MAX_EVENTS` (1000) and `MAX_SIZE_MB` (10)
- One below thresholds (no rotation)
- Windows line endings (`\r\n`)

#### 2. Error Handling Tests
- Mock file permissions → `PermissionError`
- Mock `stat()` → `OSError`
- Non-existent file handling

#### 3. Core Logic Tests
- Empty file
- Valid JSON lines
- Correct filename format: `events.20260210_143022.12.5.jsonl.rotated`

### Fixtures

- `tmp_path` - pytest built-in for temp directories
- `monkeypatch` - env var and `open()` mocking
- `freezegun` - predictable timestamps

### Coverage Target

≥80% branch coverage per project standards.

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `tests/unit/test_telemetry_rotate.py` | CREATE | Test suite |
| `scripts/telemetry_rotate.py` | REFACTOR | Result types, argparse, error handling |
| `scripts/paths.py` | EDIT | Add `repo_root()` if missing |
| `docs/ops/feature_flags.md` | EDIT | Add rotation script reference |

---

## Commits

Separate commits for each fix:

1. `test(telemetry): add boundary and error handling tests`
2. `refactor(telemetry): use Result types for error handling`
3. `fix(telemetry): add .resolve() to path calculation`
4. `refactor(telemetry): use argparse for CLI args`
5. `docs(ops): reference telemetry_rotate.py in feature_flags.md`

---

## Issues Addressed

| Severity | Issue | Status |
|----------|-------|--------|
| CRITICAL | No unit tests | ✅ Test file created |
| CRITICAL | No integration tests | ✅ CLI tests added |
| CRITICAL | Unprotected rename() | ✅ Try-except added |
| HIGH | File reading without error handling | ✅ Result types |
| HIGH | File stat without error handling | ✅ Result types |
| MEDIUM | Missing .resolve() on path | ✅ Fixed |
| MEDIUM | No structured errors | ✅ Result types |
| LOW | Inline user input parsing | ✅ argparse added |
| LOW | Documentation reference | ✅ Updated |

---

## References

- Code Review: `/cm-multi-review` (2026-02-10)
- Project Guidelines: `CLAUDE.md`
- TDD Workflow: `/metodo-develop`
- FP Methodology: `~/.claude/rules/python/`
