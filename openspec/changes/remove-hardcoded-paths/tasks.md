# Tasks: Remove Hardcoded Local Paths

## Phase 1: Foundation & Utilities

- [x] 1.1 Implement `get_repo_root()` and `get_home_path()` in `src/domain/segment_resolver.py`.
- [x] 1.2 Create `tests/conftest.py` with a global `repo_root` fixture.
- [x] 1.3 Add a `fake_home` fixture to `tests/conftest.py` to isolate skill discovery tests.

## Phase 2: Test & Script Refactoring

- [x] 2.1 Refactor `tests/acceptance/test_harness_blackbox.py`: use `repo_root` fixture for `skipif` and `cwd`.
- [x] 2.2 Refactor `tests/acceptance/test_pd_evidence_stop_e2e.py`: use `repo_root` fixture.
- [x] 2.3 Refactor `tests/unit/test_pd_regression.py`: replace hardcoded `Path` with dynamic resolution.
- [x] 2.4 Refactor `tests/unit/test_skill_hub_cards_governed.py` and `test_skill_hub_runtime_promotion.py`: use relative paths for skill fixtures.
- [x] 2.5 Update `tests/roadmap/test_prime_tripwires.py`: use flexible matching for REPO_ROOT string.
- [x] 2.6 Update `scripts/demo_sidecar_integration.sh`: use dynamic path resolution.

## Phase 3: Artifact Scrubbing

- [x] 3.1 Create `scripts/scrub_paths.py` utility for mass replacement.
- [x] 3.2 Run `scrub_paths.py` on all files in `openspec/changes/`.
- [x] 3.3 Run `scrub_paths.py` on all files in `_ctx/logs/reconcile/`.

## Phase 4: Verification

- [x] 4.1 Run unit tests for the root resolver.
- [x] 4.2 Run full acceptance test suite and verify no skips occur.
- [x] 4.3 Run `grep -r "/Users/felipe_gonzalez/" src/ scripts/ tests/` and confirm no matches (excluding binary files).
- [x] 4.4 Run `trifecta doctor` and verify health in the updated repository state.
