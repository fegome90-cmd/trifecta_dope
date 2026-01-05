### SEGMENT_NOT_INITIALIZED

```
❌ Command Failed: uv run trifecta ctx sync -s /tmp/test

Exit Code: 1
Error Class: Precondition
Error Code: SEGMENT_NOT_INITIALIZED

Cause:
Segment directory exists but is not initialized.
Missing: _ctx/trifecta_config.json

Recovery Steps:
1. Run: trifecta create -s <segment_path>
2. Verify prime file was created: ls _ctx/prime_*.md
3. Run: trifecta ctx sync -s <segment_path>
```
