# Design: Fix skill-hub --cards YAML Folded Block Parsing

## Technical Approach

Port the proven `_parse_yaml_value()` function from `register_skill.py` (lines 84-130) into `audit_skill_hub.py`, replacing the broken `parse_frontmatter()` inline extraction. The working function already handles folded (`>`), literal (`|`), quoted, and plain strings — it just hasn't been copied to the audit script. This is a surgical fix: add the function, add `import sys`, rewrite two lines in `parse_frontmatter()`.

## Architecture Decisions

### Decision: Code port vs shared module vs PyYAML

| Option | Tradeoff | Verdict |
|--------|----------|---------|
| **A: Copy `_parse_yaml_value()` into `audit_skill_hub.py`** | Duplicates 47 lines (3rd copy); but zero coupling, instant fix, matches existing pattern (already duplicated in `register_skill.py` + `bulk_register.py`) | ✅ **Chosen** |
| B: Create `yaml_utils.py` shared module | Proper DRY; requires import path setup, touches 3 files instead of 1, out of scope per proposal | ❌ Rejected |
| C: Use PyYAML `safe_load()` | Correct long-term; but the codebase deliberately avoids PyYAML for frontmatter (regex-only parsing), changing approach is scope creep | ❌ Rejected |

**Rationale**: The existing codebase has `_parse_yaml_value()` duplicated twice already (in `register_skill.py` and `bulk_register.py` with a `# Keep in sync` comment). Adding a third copy is consistent with the current pattern. A shared module is the right refactor but explicitly out of scope (per proposal).

### Decision: Error handling approach

**Choice**: Wrap in `try/except` with `sys.stderr` warning (same as existing `_parse_yaml_value()`)
**Rationale**: Malformed YAML should not crash the audit — return `None` and warn. Currently `parse_frontmatter()` has no error handling.

## Data Flow

```
SKILL.md file
     │
     ▼
read_text(skill_path)
     │
     ▼
parse_frontmatter(text)          ← modified function
     │
     ├── re.match("^---\n.*\n---\n")  → extract YAML block
     │
     ├── _parse_yaml_value(block, "name")        → NEW
     └── _parse_yaml_value(block, "description") → NEW (was naive regex)
           │
           ├─ quoted string? → strip quotes
           ├─ block indicator (>|)? → collect indented lines, join with spaces
           └─ plain string? → return as-is
     │
     ▼
SkillMeta(name, description)
     │
     ▼
build_manifest() → skills_manifest.json
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `~/.pi/agent/skills/indexing-skills-safely/scripts/audit_skill_hub.py` | Modify | Add `import sys`, add `_BLOCK_INDICATORS` frozenset, add `_parse_yaml_value()` function (47 lines), rewrite `parse_frontmatter()` to use it |

## Interfaces / Contracts

### New private function added to `audit_skill_hub.py`:

```python
_BLOCK_INDICATORS = frozenset({">", "|", ">+", ">-", "|+", "|-", ">2", ">1"})

def _parse_yaml_value(block: str, key: str) -> str | None:
    """Parse a YAML key's value, handling block scalars (> and |).
    Returns None if key not found. Returns empty string for empty block scalars.
    Wraps extraction in try/except — malformed YAML returns None with warning.
    """
```

### Modified function signature (unchanged):

```python
def parse_frontmatter(text: str) -> SkillMeta | None:
    # Still returns SkillMeta | None — callers unchanged
```

### Internal change in `parse_frontmatter()`:

Before:
```python
name_match = re.search(r"^name:\s*(.+)$", block, re.MULTILINE)
desc_match = re.search(r"^description:\s*(.+)$", block, re.MULTILINE)
if not name_match or not desc_match:
    return None
name = name_match.group(1).strip().strip('"').strip("'")
description = desc_match.group(1).strip().strip('"').strip("'")
```

After:
```python
name = _parse_yaml_value(block, "name")
description = _parse_yaml_value(block, "description")
if not name or not description:
    return None
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Manual | Verify broken descriptions fixed | `python audit_skill_hub.py --write-manifest` then `grep -c '"description": ">"' skills_manifest.json` → must be 0 |
| Manual | Verify no regressions | `python audit_skill_hub.py --report-out /tmp/report.json` — compare `suspect_descriptions` count (should drop from ~35 to 0) |
| Manual | Cards end-to-end | `skill-hub --cards "sdd"` — should return all SDD skills |

No automated test infrastructure exists for `audit_skill_hub.py`. Manual verification via the commands above is the approach.

## Verification Commands

```bash
# BEFORE fix (establishes baseline)
cd ~/.pi/agent/skills/indexing-skills-safely/scripts
python audit_skill_hub.py --report-out /tmp/before.json
# Check: suspect_descriptions count should be ~35

# AFTER fix
python audit_skill_hub.py --write-manifest --report-out /tmp/after.json
# Check: suspect_descriptions count should be 0
python -c "import json; d=json.load(open('/tmp/after.json')); print(len([s for s in d['antipatterns']['suspect_descriptions']]))"

# E2E verification
skill-hub --cards "sdd gate"
# Should return multiple SDD skills (was returning only 1 before)
```

## Migration / Rollout

No migration required. The manifest is regenerated from source files — just re-run `audit_skill_hub.py --write-manifest` after the fix.

**Rollback**: Revert `audit_skill_hub.py` to previous version. No data loss possible since manifest is always regenerated from SKILL.md files.

## Open Questions

- None. The fix is self-contained with clear verification criteria.
