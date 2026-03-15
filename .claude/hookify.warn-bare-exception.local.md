---
name: warn-bare-exception
enabled: true
event: file
pattern: except\s+Exception\s*:
---

⚠️ **BARE EXCEPTION CATCH DETECTED**

Catching `Exception` without logging or specific handling can hide errors and make debugging difficult.

**Best practices:**
1. Catch specific exceptions: `except (ValueError, KeyError) as e:`
2. If you must catch Exception, log it: `except Exception as e: logger.debug(f"...")`
3. Use `typing.Any` alternatives: `object` with `isinstance()` runtime check

**Example fix:**
```python
# Instead of:
except Exception:
    return {}

# Use:
except (yaml.YAMLError, OSError, ValueError) as e:
    logger.debug(f"Failed to load: {e}")
    return {}
```
