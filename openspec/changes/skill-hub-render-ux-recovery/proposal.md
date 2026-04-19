# Proposal: Skill Hub Render UX Recovery

## Intent

Recover the old `skill-hub` first-impression UX — big banner, sentence-query guidance, and error-driven orchestration feel — while keeping all runtime authority inside the governed pipeline and **not** reviving hidden-authority legacy surfaces.

## Scope

### In Scope
- Add a governed terminal intro/guidance path for `scripts/skill-hub`.
- Route empty/unsupported/malformed states through `src/cli/error_cards.py` instead of shell-echoed ad hoc output.
- Keep card rendering authority in `src/cli/skill_cards.py` and planning/classification in `scripts/skill_hub_cards_core.py`.

### Out of Scope
- Reviving `/Users/felipe_gonzalez/.local/bin/skill_hub_info_card.py` or any `~/.local/bin` legacy script as runtime authority.
- Changing canonical admission/promotion rules from `openspec/specs/skill-hub-authority/spec.md`.
- Broad CLI redesign outside the `skill-hub` path.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `skill-hub-authority`: runtime-visible UX changes now include governed intro/banner framing and query guidance, while preserving canonical-only authority, fail-closed behavior, and non-authoritative legacy compatibility inputs.

## Approach

Implement a small repo-owned UX composer called by `scripts/skill-hub` that emits the banner + sentence-query guidance before delegating to governed classifier/renderers. Keep the classifier in `scripts/skill_hub_cards_core.py`, approved-card rendering in `src/cli/skill_cards.py`, and fail-closed surfaces in `src/cli/error_cards.py`. Treat legacy home-bin artifacts as comparison-only, not canonical runtime.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `scripts/skill-hub` | Modified | Entry orchestration and first-impression UX |
| `scripts/skill_hub_cards_core.py` | Modified | Preserve authority for classify/render plan |
| `src/cli/skill_cards.py` | Modified | Optional intro/header helper reuse |
| `src/cli/error_cards.py` | Modified | Fail-closed orchestration frames |
| `docs/contracts/SKILL_HUB_CARDS_GOVERNED_CONTRACT.md` | Modified | Clarify governed UX boundary |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| UX drift reintroduces hidden authority | Med | Keep legacy `~/.local/bin` scripts out of the runtime path and codify governed ownership in spec |
| Terminal output regressions | Med | Preserve stdout/stderr separation and existing exit codes |
| Hybrid persistence gap in this parent runtime | High | Filesystem `proposal.md` is the source of truth here; Engram save is unavailable in this runtime |

## Rollback Plan

Revert the new UX composer path and restore the current governed planner/classifier flow in `scripts/skill-hub`, leaving canonical authority and exit codes unchanged. Do **not** roll back to any `~/.local/bin` legacy surface.

## Dependencies

- Existing governed skill-hub contract at `openspec/specs/skill-hub-authority/spec.md`.

## Success Criteria

- [ ] `skill-hub` shows the banner + sentence-query guidance without calling hidden-authority home-bin helpers.
- [ ] Unsupported/error states use governed error cards and preserve fail-closed exit codes.
- [ ] No legacy `~/.local/bin/*` surface becomes canonical runtime behavior.
