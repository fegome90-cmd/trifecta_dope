### Validation Invariants

The `validate` command checks:

- Schema version is correct (int)
- All `index.id` exist in `chunks.id`
- `source_files` are consistent with disk
- Size and budget limits are reasonable
- Segment is sanitized (no path traversal)
