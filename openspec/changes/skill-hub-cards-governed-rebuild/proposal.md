# Proposal: skill-hub cards governed rebuild

## Intent
Reconstruct the verified `skill-hub` cards slice on a clean authority surface so the public wrapper, governed helper, thin deprecated shim, and targeted tests all match the canonical `skill-hub-authority` contract without reviving unrelated or unverified changes.

## Scope

### In Scope
- Restore `scripts/skill-hub` support for `--cards` and `--limit`.
- Route card rendering through the governed `scripts/skill-hub-cards` entrypoint only.
- Keep `scripts/skill_hub_cards.py` as a thin deprecated shim.
- Carry the governed parser/classifier implementation in `scripts/skill_hub_cards_core.py`.
- Preserve targeted tests for wrapper contract and governed card classification.

### Out of Scope
- Any `skill_manifest.py` marker-based migration logic.
- Admission, promotion, or pack publication refactors.
- Generic repo cleanup outside the reconstruction slice.

## Why now
The previous closeout surface mixed narrative and code authority. This rebuild creates one honest implementation slice backed by real files and passing tests before any further archive or cleanup step.
