### F. TOKEN ESTIMATION AUDIT

**Current:** [src/infrastructure/telemetry.py#L66-L111](src/infrastructure/telemetry.py#L66-L111)

```python
def _estimate_tokens(self, text: str) -> int:
    """Rough token estimation: 1 token ≈ 4 characters."""
    if not text:
        return 0
    cleaned = " ".join(str(text).split())
    return max(1, len(cleaned) // 4)
```

**Status:** ✅ Already tracks tokens per command (input, output, retrieved).

**For AST/LSP:** Not needed (no LLM context), but can track bytes_read instead.

---
