### PRIME_FILE_NOT_FOUND

```
❌ Command Failed: uv run trifecta ctx get -s . --ids prime:abc

Exit Code: 1
Error Class: Runtime
Error Code: PRIME_FILE_NOT_FOUND

Cause:
Expected prime file not found: _ctx/prime_<segment>.md

Recovery Steps:
1. Check segment directory structure
2. Run: trifecta refresh-prime -s <segment_path>
3. Verify _ctx/prime_*.md exists
```
