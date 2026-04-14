# Verify Report: skill-hub cards governed rebuild

## Verdict
PASS with scoped warnings.

## Verified evidence
- `scripts/skill-hub` now owns `--cards` / `--limit` parsing and delegates cards mode to the adjacent governed helper only.
- `scripts/skill-hub-cards` is a thin governed executable entrypoint.
- `scripts/skill_hub_cards_core.py` owns card parsing, normalization, classification, and rendering logic.
- `scripts/skill_hub_cards.py` remains a deprecated shim rather than a rival authority surface.
- Targeted tests passed: 18/18 in `test_skill_hub_cards_wrapper_contract.py` and `test_skill_hub_cards_governed.py`.

## Alignment with canonical SSOT
- The rebuilt slice aligns with the **canonical-only downstream consumption** requirement by ensuring cards mode flows through one governed helper path instead of multiple competing entrypoints.
- The rebuilt slice also aligns with the **fail-closed** intent of the authority contract by classifying metadata-only and unsupported hits as non-renderable rather than claiming success.

## Scoped warnings
- This rebuild does **not** implement or claim the broader admission/promotion requirements from `openspec/specs/skill-hub-authority/spec.md`; those remain outside this slice.
- No marker-based `skill_manifest.py` migration logic was verified, so it is intentionally excluded from this change.
- Transient forensic surfaces still exist and must be cleaned up during closeout per the re-anchor pack.

## Archive readiness
- **Not ready yet** for archive.
- Resolved: the failed `skill-hub-authority-anchor-closeout` worktree and local branch were retired after preserving the cleanup review.
- Blocker 1: `skill-hub-authority-anchor-mergefix` still contains unrelated daemon/runtime edits that require a separate decision before that surface can be removed.
- Blocker 2: `stash@{0}` still exists as imported forensic residue and should only be dropped after the remaining mergefix cleanup path is settled.
- Blocker 3: the mergefix review now identifies three bundles, but Bundle 2 (daemon/runtime code and its paired tests) has not yet been accepted, migrated, or discarded.
