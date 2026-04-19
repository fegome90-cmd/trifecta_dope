# Proposal: Add OpenCode Skills as Skill-Hub Source Root

## Intent

20 unique skills exist ONLY in `~/.config/opencode/skills/` — invisible to the skill-hub's indexing pipeline. They cannot be discovered by any agent via `trifecta ctx search`. Meanwhile, 23 overlapping OpenCode skills are already indexed from other roots (identical content). Adding opencode-skills as a source root closes this discovery gap and makes the orchestrator runtime's skills fully searchable.

## Scope

### In Scope
- Add `opencode-skills` (priority 4) to SOURCE_ROOTS in `register_skill.py`, `bulk_register.py`, and `sources.yaml`
- Fix frontmatter parser to handle YAML block scalars (`description: >`) — currently regex `^description:\s*(.+)$` matches literal `>`
- Fix name validation regex to allow underscores: `[a-z0-9_-]+` instead of `[a-z0-9-]+`
- Bulk-register 20 unique OpenCode skills after parser fixes
- Document priority order in `indexing-skills-safely/SKILL.md`

### Out of Scope
- Renaming existing OpenCode skill directories (use underscore-tolerant regex instead)
- Modifying the 23 duplicate skills (already indexed from higher-priority roots)
- Running `skill-workflow` normalization on 18 skills with frontmatter issues (separate task)
- Changes to `audit_skill_hub.py` (reads from sources.yaml, not hardcoded list)

## Capabilities

### Modified Capabilities
- `skill-indexing-pipeline`: SOURCE_ROOTS list and frontmatter parsing rules change to support a new root and broader name/description formats

## Approach

**Phase 1 — Parser Fixes** (register_skill.py, bulk_register.py):
1. Relax name regex: `[a-z0-9_-]+` (allows underscores)
2. Fix description parser: detect block scalar `>` / `|`, read until next YAML key or `---`

**Phase 2 — Source Root Addition** (3 files):
1. Add `("opencode-skills", Path("~/.config/opencode/skills").expanduser())` at position 4 in both SOURCE_ROOTS lists
2. Add entry to `sources.yaml` with priority 4, shifting existing 4-7 → 5-8

**Phase 3 — Bulk Registration**:
1. Dry-run `bulk_register.py --source opencode-skills`
2. Live run → 20 unique skills registered
3. Verify: `trifecta ctx search <skill-name>` for each unique skill

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `register_skill.py` | Modified | SOURCE_ROOTS + name regex + desc parser |
| `bulk_register.py` | Modified | SOURCE_ROOTS + name regex + desc parser |
| `sources.yaml` | Modified | New opencode-skills entry, priority renumber |
| `indexing-skills-safely/SKILL.md` | Modified | Priority docs update |
| `~/.config/opencode/skills/` | Read-only | Source scan, no modifications |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Underscore in name conflicts with existing entries | Low | `trifecta ctx search` already handles hyphens; underscores are additive |
| Block scalar parser breaks on multi-line descriptions | Med | Fallback: normalize frontmatter in 9 PAE skills manually |
| Priority 4 shadows codex-skills for overlapping skills | Low | 23 duplicates identical; higher-priority root already wins |
| sources.yaml renumber breaks external consumers | Low | audit_skill_hub.py reads dynamically; no hardcoded priority refs |

## Rollback Plan

1. Revert SOURCE_ROOTS addition in both .py files (single line each)
2. Remove opencode-skills entry from sources.yaml
3. Run `bulk_register.py --skip-existing` to re-sync without opencode
4. No data loss — skills are registered, not moved

## Dependencies

- `skill-workflow` at `~/.pi/agent/skills/skill-workflow/` available for future normalization (not this change)
- `trifecta` CLI must be functional for `trifecta ctx sync`

## Success Criteria

- [ ] `trifecta ctx search mr-plan` returns result from opencode-skills root
- [ ] `trifecta ctx search pae-generator` returns result (currently invisible)
- [ ] `bulk_register.py --dry-run --source opencode-skills` reports 20 skills
- [ ] Zero duplicate entries created (23 existing skills stay at higher-priority root)
- [ ] Name validation accepts `horror_cosmico_lovecraftiano` (underscores)
- [ ] Description parser handles `description: >` block scalars
