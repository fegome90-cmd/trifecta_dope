### Size & Time Limits
| Limit | Value | Action |
|-------|-------|--------|
| **Max file to parse** | 1MB | Skip + warn if >1MB |
| **Max skeleton size** | 10% of source | Fail if expansion >10% |
| **Max LSP latency** | 500ms | Timeout + fallback |
| **Max symbols per file** | 1000 | Truncate + warn if >1000 |

---
