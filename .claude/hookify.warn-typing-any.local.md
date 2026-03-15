---
name: warn-typing-any
enabled: true
event: file
pattern: :\s*Any\s*=|->\s*Any|:\s*Any\b(?!_)
---

⚠️ **TYPING.ANY DETECTED**

Using `typing.Any` defeats type checking and can hide bugs.

**Better alternatives:**
1. Use `object` with runtime `isinstance()` check
2. Use union types: `str | int | None`
3. Use `Unknown` for truly unknown types (Python 3.14+)
4. Use `typing.Protocol` for duck typing

**Example fix:**
```python
# Instead of:
data: Any = yaml.safe_load(f)

# Use:
data: object = yaml.safe_load(f)
if not isinstance(data, dict):
    return {}
```

**Note:** `Any` is acceptable in TYPE_CHECKING blocks for circular imports.
