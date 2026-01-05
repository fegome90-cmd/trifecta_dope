### D.2 Redaction Filter for Diagnostics

**If LSP emits diagnostics with snippets, redact before logging:**

```python
def _redact_code_snippet(snippet: str) -> str:
    """Hash code, don't log actual content."""
    import hashlib
    return f"sha256:{hashlib.sha256(snippet.encode()).hexdigest()[:12]}"

# In DiagnosticsCollector
def _on_diagnostics(self, params):
    uri = params["uri"]
    diags = params.get("diagnostics", [])

    # Redact message if contains code
    for diag in diags:
        if "source" in diag and "message" in diag:
            diag["message"] = diag["message"][:100]  # Truncate
            # Don't log the actual error snippet

    self.diagnostics[uri] = diags
```

---
