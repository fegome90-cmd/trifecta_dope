### E. SECURITY & REDACTION AUDIT

**Current redaction:** [src/infrastructure/telemetry.py#L206](src/infrastructure/telemetry.py#L206)

```python
def _sanitize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Truncate and sanitize arguments based on level."""
    safe = {}
    for k, v in args.items():
        if k == "query" and isinstance(v, str):
            safe[k] = v[:120]  # Truncate query ✅
        elif k in ["ids", "segment", "limit", "mode", "budget_token_est", "task"]:
            if k == "task" and isinstance(v, str):
                safe[k] = v[:120]  # Truncate task ✅
            else:
                safe[k] = v
        # Skip unknown args for safety ✅
    return safe
```

**Findings:**
- ✅ Queries truncated to 120 chars
- ✅ Unknown args dropped
- ⚠️ Segment field still logged (full absolute path)
  - **Mitigation:** In AST/LSP, use relative paths (relative_to() or filename only)

**New redaction rules (for AST/LSP):**
| Data | Current | Proposed |
|------|---------|----------|
| File paths | Full absolute | ✅ Relative (src/domain/models.py) |
| File content | Not logged | ✅ Keep (no content) |
| Line numbers | ✅ Logged | ✅ Keep (structural) |
| Symbol names | ✅ Logged | ✅ Keep (public) |
| Diagnostics | Not yet | ✅ Truncate/hash (no code snippets) |

**Security Status:** ✅ **APPROVED**. New redaction rules implemented in audit doc.
