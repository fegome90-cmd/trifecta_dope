# Proposal: Fix skill-hub --cards YAML Folded Block Parsing

## Intent

35 of 467 skills (7.5%) fail card promotion because `skills_manifest.json` stores `"description": ">"` instead of the actual text. The root cause is `audit_skill_hub.py::parse_frontmatter()` which uses a naive regex that captures the literal `>` character from YAML folded block scalars (`description: >`).

## Scope

### In Scope
- Fix `audit_skill_hub.py::parse_frontmatter()` to handle YAML folded (`>`) and literal (`|`) block scalars
- Regenerate `skills_manifest.json` after fix (rebuilds all 467 entries)
- Verify 35 previously-broken skills now have valid descriptions in manifest

### Out of Scope
- Normalizing SKILL.md files (they are valid YAML — the parser is the bug)
- Refactoring shared YAML parsing into a common module (stretch goal, separate change)
- Adding fallback description extraction in card promotion code (masks the real bug)

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `skill-hub-authority`: Manifest generation must correctly parse all valid YAML frontmatter shapes (quoted strings, folded blocks, literal blocks).

## Approach

The `_parse_yaml_value()` function in `register_skill.py` (lines 80-126) and `bulk_register.py` (lines 55-101) already handles block scalars correctly. The fix is to port this logic into `audit_skill_hub.py::parse_frontmatter()` (line 70-83).

**Specific change**: Replace the naive `re.search(r"^description:\s*(.+)$", ...)` in `parse_frontmatter()` with block-scalar-aware extraction that:
1. Detects block indicators (`>`, `|`, `>+`, `>-`, etc.)
2. Collects indented continuation lines
3. Joins with spaces (folded) or newlines (literal)

**Verification**: Run `audit_skill_hub.py --write-manifest`, then count entries where `description == ">"` — must be 0.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `~/.pi/agent/skills/indexing-skills-safely/scripts/audit_skill_hub.py` | Modified | Fix `parse_frontmatter()` to handle block scalars |
| `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json` | Regenerated | Rebuild to fix 35 broken entries |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Regex change breaks existing quoted-string parsing | Low | Unit test both quoted and block scalar cases |
| Manifest regeneration changes entry ordering | Low | `build_manifest()` sorts by `(name, source, path)` — deterministic |
| Edge case: multi-line folded blocks with blank lines | Med | Port the full `_parse_yaml_value()` logic, not a simplified version |

## Rollback Plan

Revert `audit_skill_hub.py` to previous version. Manifest is regenerated from source files — no data loss.

## Dependencies

- Access to `~/.pi/agent/skills/indexing-skills-safely/scripts/` (write permission)
- Python 3.12+ (no new dependencies)

## Success Criteria

- [ ] `parse_frontmatter()` correctly extracts descriptions from YAML folded block scalars
- [ ] 0 skills in manifest have `"description": ">"`
- [ ] `skill-hub --cards` returns results matching `skill-hub` search counts for affected skills
- [ ] Existing quoted-string and plain-text descriptions still parse correctly
