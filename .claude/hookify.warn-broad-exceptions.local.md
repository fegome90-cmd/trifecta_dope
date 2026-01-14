---
name: warn-broad-exceptions
enabled: true
event: file
action: warn
pattern: except\s+(Exception|BaseException)\s*:\s*$
---

⚠️ **Broad Exception Handling Detected**

You're catching `Exception` or `BaseException`, which masks bugs and makes debugging difficult.

**Why this matters:**
- Catches `KeyboardInterrupt`, `MemoryError`, `ImportError` - system errors that shouldn't be silenced
- Hides programming errors like `AttributeError`, `TypeError`, `NameError`
- Makes production debugging nearly impossible
- Violates project's explicit rules against silent failures

**Better approach:**
```python
# ❌ Too broad
except Exception as e:
    logger.error(f"Error: {e}")

# ✅ Specific exceptions
except (FileNotFoundError, PermissionError, ValueError) as e:
    logger.error(f"Error: {e}")

# ✅ Let unexpected errors propagate
except ValueError as e:
    logger.error(f"Validation error: {e}")
# Other exceptions will propagate and be caught by proper error handlers
```

**Common specific exceptions to use:**
- File I/O: `FileNotFoundError`, `PermissionError`, `UnicodeDecodeError`
- Data: `ValueError`, `TypeError`, `KeyError`
- Network: `ConnectionError`, `TimeoutError`
- OS: `OSError`, `ProcessLookupError`

**Code review reference:** Issue #1-#4 from silent-failure-hunter agent identified 6 critical broad exception catches.

**If this is a genuine catch-all scenario:**
Document why in a comment and consider adding `raise` to re-raise after logging.
