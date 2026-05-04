# Proposal: Skill Hub Surgical Repair

## Intent

Repair `skill-hub` contract drift without broadening runtime authority: live skill refs, segment-aware linting, card rendering, intro/banner behavior, and registered-entry recovery must all flow through governed sources and promotion tooling.

## Scope

### In Scope
- Support exact live `skill:{name}:` alias canonical refs alongside legacy `repo:{name}.md:`.
- Make query linting segment-aware so `skills-hub` avoids vague `agent.md` / `prime.md` defaults.
- Establish one card authority between governed runtime core and `SkillCardViewModel` expectations.
- Route card rendering through unified `_select_renderer` dispatch with TTY-aware plain/rich handoff.
- Pin/fix intro/banner behavior for plain vs rich runtime output.
- Resolve broken registered entries only via governed `skill-hub-runtime promote/verify`.

### Out of Scope
- Manual manifest, receipt, or promoted-target edits.
- Expanding promoted runtime to arbitrary `src/` modules unless design proves it necessary.

## Capabilities

### New Capabilities
- `skill-hub-runtime-ux`: Runtime card view-model, renderer handoff, and intro/banner output contracts.

### Modified Capabilities
- `skill-hub-authority`: Extend canonical downstream consumption to live `skill:*` refs, segment-scoped lint defaults, and governed-only promotion recovery.

## Authority Surfaces

| Surface | Owner | Writer |
|---------|-------|--------|
| Alias canonical-match | `scripts/skill-hub` | Alias rerank predicate |
| Query lint defaults | `src/domain/query_linter.py` | Segment-profile selector |
| Card renderable state | `scripts/skill_hub_cards_core.py` | Adapter boundary |
| Intro/banner output | `scripts/skill_hub_runtime_ux.py` | Runtime UX renderer |
| Registration recovery | `scripts/skill-hub-runtime` | Promote/verify tooling |

## Approach

Surgical governed-runtime repair. Keep `scripts/` promoted artifacts as the runtime surface, add exact canonical ref recognition for both supported shapes, pass an explicit segment/profile into linting, and make the card adapter boundary the single owner of renderable card state. Treat receipts as evidence, not authority.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `scripts/skill-hub` | Modified | Alias canonical-match predicate accepts exact live skill refs. |
| `src/domain/query_linter.py` | Modified | Segment/profile-aware vague-query defaults. |
| `scripts/skill_hub_cards_core.py` | Modified | Single runtime card/view-model adapter contract. |
| `scripts/skill_hub_runtime_ux.py` | Modified | Pinned banner/intro behavior. |
| `scripts/skill-hub-runtime` | Modified | Promote/verify remains sole registration repair path. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Loose alias matching creates false canonicals | Med | Match exact ref families only. |
| Card model authority stays split | Med | Name one writer in spec/design before implementation. |
| Linter profile leaks environment coupling | Med | Use explicit caller-provided segment/profile. |

## Rollback Plan

Revert the change branch and rerun `scripts/skill-hub-runtime verify`; last valid promoted set remains authoritative because no receipts or targets are edited manually.

## Dependencies

- Existing `skill-hub-authority` spec.
- Governed `scripts/skill-hub-runtime promote/verify` flow.

## Success Criteria

- [ ] Alias rerank recognizes `skill:{name}:` and legacy refs without substring matching.
- [ ] `skills-hub` vague queries do not receive `agent.md` / `prime.md` defaults.
- [ ] Runtime cards have one explicit authority and adapter contract.
- [ ] Intro/banner expectations are pinned by tests.
- [ ] Registration repair evidence comes from promote/verify, not manual edits.
