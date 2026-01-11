### Redaction in Telemetry (No Code, Only Hashes)
```python
REDACT_PATTERNS = [
    r"https?://[^/\s]+",              # URLs
    r"[A-Za-z0-9._%+-]+@[^@]+",       # Emails
    r"(sk_|pk_)[a-zA-Z0-9]{32,}",     # API keys
]

def redact_for_telemetry(text: str) -> str:
    """Remove sensitive patterns before logging."""
    for pattern in REDACT_PATTERNS:
        text = re.sub(pattern, "[REDACTED]", text)
    return text

# Usage:
telemetry.event("symbol.resolve", {
    "file": target_file.name,  # Just filename, not full path
    "symbol": symbol_name,
    "diagnostics": redact_for_telemetry(diag_text)  # Strip secrets
}, ...)
```
