# Apply Progress: doctor-ranking-optimization

## Completed

- Added `tests/unit/test_skill_hub_doctor_alias.py` with red/green coverage for the three weak doctor phrases.
- Added `resolve_doctor_alias_match()` to `scripts/skill-hub`.
- Mapped only:
  - `exit code drift`
  - `no me aparecen skills`
  - `hub de skills`
- Reused existing canonical alias output path.
- Promoted runtime with `scripts/skill-hub-runtime promote`.
- Verified runtime with `scripts/skill-hub-runtime verify`.

## Verification During Apply

- Red test first: `tests/unit/test_skill_hub_doctor_alias.py` failed because no canonical alias was printed.
- Green test after patch: `2 passed`.
- Focused regression: `6 passed`.
- Source smoke: three weak phrases now print `Canonical alias match: skill-hub-doctor`.
- Promoted runtime smoke: same behavior verified via `~/.local/bin/skill-hub`.

## Files Changed

- `scripts/skill-hub`
- `tests/unit/test_skill_hub_doctor_alias.py`
- `openspec/changes/doctor-ranking-optimization/*`
