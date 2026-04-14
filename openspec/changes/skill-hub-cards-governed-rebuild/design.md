# Design: skill-hub cards governed rebuild

## Technical approach
Keep the reconstruction narrow and authority-safe:

1. `scripts/skill-hub` owns public CLI flag parsing and delegates cards mode.
2. `scripts/skill-hub-cards` is the governed executable entrypoint and stays thin.
3. `scripts/skill_hub_cards_core.py` owns parsing, normalization, classification, and rendering.
4. `scripts/skill_hub_cards.py` remains a deprecated compatibility shim only.
5. Targeted tests lock wrapper propagation and governed classification behavior.

## Why this shape
This split preserves a single operational path for cards mode, keeps the public wrapper stable, and prevents the old rival Python entrypoint from becoming a second authority surface.

## Tradeoffs
- Keeping a deprecated shim costs one extra file, but it avoids abrupt breakage for legacy callers.
- The rebuild intentionally does not claim manifest/admission changes because no verified implementation evidence exists for that slice.

## Verification
- Wrapper contract tests prove stdout/stderr/exit propagation.
- Governed runtime tests prove metadata-only and unsupported hits fail closed while renderable skills succeed.
