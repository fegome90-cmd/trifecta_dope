# Proposal: repair global skill frontmatter

## Intent
Repair the broken global `skill-hub` entries caused by invalid YAML frontmatter in external `SKILL.md` files so discovery metadata becomes parseable again without changing skill intent or introducing runtime-side workarounds.

## Scope
### In Scope
- Fix the 14 currently broken external `SKILL.md` files referenced by the live global manifest.
- Normalize invalid frontmatter quoting/escaping/list syntax while preserving the semantic meaning of `name`, `description`, `search_hints`, and `metadata`.
- Add repo-side diagnostics/tests that make malformed global skill frontmatter auditable before the hub silently degrades.
- Document the exact broken set, ownership boundaries, and rollback path.

### Out of Scope
- Rewriting unrelated skill bodies or changing skill behavior beyond frontmatter validity.
- Rebalancing search ranking, source priority, or hub runtime routing.
- Hand-patching generated `skills_manifest.json` / `context_pack.json` as a substitute for fixing source files.
- Repairing every future malformed skill automatically without an explicit source-author fix.

## Capabilities
### New Capabilities
- None.

### Modified Capabilities
- `skill-hub-authority`: upstream source quality and doctor-style auditing of malformed external frontmatter.
- `indexing-skills-safely`: validation expectations for external skill registration and refresh.

## Approach
1. Freeze the known broken set from the live manifest and classify each file by YAML failure mode.
2. Add a repo-owned audit surface that proves which manifest entries fail frontmatter parsing and why.
3. Apply source-author fixes only to the broken external `SKILL.md` files, using minimal quoting/structure changes.
4. Re-run the audit to prove the broken set reaches zero without changing semantic ownership or hub generation rules.

## Affected Areas
| Area | Impact | Description |
|------|--------|-------------|
| `openspec/changes/repair-global-skill-frontmatter/*` | New | SDD artifacts for the repair effort. |
| Repo tests/audit tooling | Planned modify | Add deterministic audit coverage for malformed external frontmatter referenced by the live manifest. |
| External skill sources under `~/.claude/skills`, `~/.pi/agent/skills`, and `~/Developer/examen_grado/skills` | Planned modify | Minimal frontmatter repairs in 14 files. |
| Generated hub artifacts | Derived | Must be regenerated only after source-author fixes, never patched directly. |

## Risks
| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Editing external skills changes retrieval wording unexpectedly | Med | Keep fixes syntax-only where possible; preserve field values semantically. |
| Generated hub state stays stale after source fixes | High | Require explicit post-fix rebuild/audit of the hub, not assumptions. |
| Repo adds diagnostics but cannot repair sources due to permissions | High | Treat source edits as a separately approved apply step; keep artifacts explicit about the block. |
| One malformed fix introduces new YAML drift | Med | Add per-file audit assertions and verify after each batch. |

## Rollback Plan
1. Revert the external `SKILL.md` edits file-by-file from backup or git history in their owning locations.
2. Re-run the audit to confirm the previously broken set returns, proving rollback accuracy.
3. Rebuild the generated hub artifacts from the restored sources; do not patch generated manifest state by hand.

## Dependencies
- Live global manifest at `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json` remains the discovery baseline.
- Approval is required to modify external skill files outside this repository sandbox.

## Success Criteria
- [ ] All 14 currently broken manifest entries parse as valid YAML frontmatter.
- [ ] The broken set is auditable from repo-owned tooling/tests, not manual inspection only.
- [ ] No generated hub artifact is manually edited as part of the repair.
- [ ] The final audit proves zero broken entries in the previously failing set.
