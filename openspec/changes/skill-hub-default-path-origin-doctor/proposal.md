# Proposal: skill-hub default path origin doctor

## Intent
Diagnose and fix the `skill-hub` split-brain where default-path UX and cards-path activation diverge. This is **not** a banner-only fix: the bug spans CLI flag parsing, promoted artifact drift, and authority boundaries between repo scripts and `~/.local/bin`.

## Scope
### In Scope
- Reconcile CLI parsing so `--cards` is not position-sensitive.
- Restore the default-path intro/render contract without making search output the authority.
- Align promoted runtime artifacts with the repo source of truth.
- Clarify single-writer ownership for each authority surface.

### Out of Scope
- New search/ranking behavior.
- Broader skill discovery UX redesign.
- Generic fallback semantics for invalid `skill_hub` packs.

## Capabilities
### New Capabilities
- None.

### Modified Capabilities
- `skill-hub-authority`: CLI admission, promoted artifact set, and downstream consumption contract are changing.

## Approach
Treat this as a contract reconciliation:
1. Make the CLI flag/argument contract explicit and order-independent where needed.
2. Declare one writer per authority surface: repo scripts own source behavior, the promotion step owns `~/.local/bin`, and the authority spec owns semantics.
3. Ensure the promoted artifact set is complete and matches the repo contract.
4. Separate the default surface from the cards surface so each has one authoritative entrypoint.

## Affected Areas
| Area | Impact | Description |
|------|--------|-------------|
| `openspec/specs/skill-hub-authority/spec.md` | Modified | Reconcile authority contract for parsing, promotion, and consumption. |
| `scripts/skill-hub` | Likely Modified | Normalize CLI parsing and default-path behavior. |
| `scripts/skill-hub-cards` | Likely Modified | Preserve cards entrypoint contract. |
| `scripts/skill_hub_cards_core.py` | Likely Modified | Preserve semantic admission/routing authority under one shared contract. |
| `scripts/skill-hub-runtime` | Likely Modified | Enforce canonical promoted artifact map, receipt completeness, and doctor/verify ownership. |
| `scripts/skill_hub_runtime_ux.py` | Likely Modified | Default intro/render behavior. |

## Risks
| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Breaking existing `skill-hub` invocation patterns | Med | Preserve compatibility while making flags explicit and tested. |
| Partial promotion leaves repo/bin drift | High | Promote the full artifact set atomically, never piecemeal. |
| Confusing evidence with authority | Med | Keep logs/probes diagnostic only; specs own contract decisions. |

## Rollback Plan
If the new contract regresses behavior, repromote the last known-good `skill-hub` artifact set and restore the previous CLI parsing path. Do not patch `~/.local/bin` ad hoc; roll back the full promoted set together so repo and runtime stay aligned.

## Dependencies
- Existing `skill-hub-authority` spec as the contract anchor.

## Success Criteria
- [ ] `skill-hub "query" --cards` activates cards without requiring positional `--cards`.
- [ ] Default-path UX emits the intended intro/render behavior.
- [ ] Repo scripts and promoted artifacts describe the same authority surface.
- [ ] The spec names one owner/writer per surface.
