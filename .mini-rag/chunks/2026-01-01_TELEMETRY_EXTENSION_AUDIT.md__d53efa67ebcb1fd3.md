### D.1 No Sensitive Data in Telemetry

**Redaction rules (HARD):**

| Data Type | Example | Allowed in Telemetry? | How |
|-----------|---------|----------------------|-----|
| Full file path | `/Users/..../myfile.py` | ❌ NO | Use relative path (`src/domain/models.py`) or just filename |
| File content | `config = {"API_KEY": "sk_..."}` | ❌ NO | Use hash or size only |
| API keys, tokens | `sk_abc123def...` | ❌ NO | Redact in args before sending |
| User home dir | `/Users/alice/...` | ❌ NO | Use segment-relative path |
| Query text | `"find secrets in my code"` | ⚠️ TRUNCATED | Truncate to 120 chars (existing behavior) |
| Symbol names | `ContextService`, `search_by_symbol` | ✅ YES | Public names, non-sensitive |
| Line numbers | 42, 150, 200 | ✅ YES | Structural info, non-sensitive |

**Implementation in ast_lsp.py:**
```python
def _relative_path(path: Path, segment_root: Path) -> str:
    """Convert to relative path for telemetry."""
    try:
        return str(path.relative_to(segment_root))
    except ValueError:
        return str(path.name)  # Fallback to filename only

# Usage
telemetry.event(
    "ast.parse",
    {"file": _relative_path(file_path, segment_root)},  # ← NO absolute path
    {...},
    ...,
)
```
