# BUG: `trifecta create -s <target>` writes to CLI cwd, not target directory

## Status
**FIXED** - 2026-01-02

## Description
When running `trifecta create -s /path/to/target`, the command creates files in the **CLI's current working directory**, not in the specified target directory.

## Evidence

### Command
```bash
cd /tmp/test_dogfood
uv run --directory /path/to/trifecta_dope trifecta create -s .
```

### Expected
Files created in `/tmp/test_dogfood/_ctx/`:
- `prime_test_dogfood.md`
- `agent_test_dogfood.md`
- `session_test_dogfood.md`

### Actual
Files created in `/path/to/trifecta_dope/_ctx/`:
- `prime__.md` (empty segment_id!)
- `agent__.md`
- `session__.md`

### stdout
```
✅ Trifecta created at /path/to/trifecta_dope  # Wrong path!
   ├── skill.md
   ├── readme_tf.md
   ├── _ctx/prime__.md                          # Empty segment_id
   ├── _ctx/agent__.md
   ├── _ctx/session__.md
```

## Impact
- **Cannot dogfood `create→refresh-prime→sync` workflow in acceptance tests**
- Segment ID derived incorrectly (empty string)
- Files pollute CLI repo instead of target

## Root Cause (suspected)
The `create` command likely uses `Path.cwd()` instead of resolving the `-s` argument to an absolute path.

## Workaround
Manually create `_ctx/` structure with correct naming:
```python
ctx_dir = segment / "_ctx"
ctx_dir.mkdir()
prime_file = ctx_dir / f"prime_{segment.name}.md"
prime_file.write_text(...)
```

## Affected Tests
- `test_ctx_sync_succeeds_after_initialization` - SKIPPED pending fix

## Fix Priority
HIGH - Blocks agent onboarding and acceptance testing
