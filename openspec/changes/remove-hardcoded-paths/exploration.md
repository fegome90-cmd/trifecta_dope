## Exploration: Remove Hardcoded Local Paths

### Current State
The project contains several instances of hardcoded absolute paths pointing to the user's home directory (`<REPO_ROOT>/`). These are primarily used in:
- `pytest.mark.skipif` conditions in tests.
- Path arguments for UseCases in unit tests.
- Working directory definitions in acceptance tests.
- Shell scripts for demo integrations.
- SDD artifacts and log fixtures.

This creates machine-dependency and prevents tests from running in CI or other environments.

### Affected Areas
- `tests/acceptance/test_harness_blackbox.py`
- `tests/acceptance/test_pd_evidence_stop_e2e.py`
- `tests/unit/test_pd_regression.py`
- `tests/unit/test_skill_hub_cards_governed.py`
- `tests/unit/test_skill_hub_runtime_promotion.py`
- `tests/roadmap/test_prime_tripwires.py`
- `scripts/demo_sidecar_integration.sh`
- `tests/fixtures/**/*` (log and patch files)
- `openspec/changes/**/*` (documentation)

### Approaches
1. **Dynamic Root Resolution (Recommended)**
   - Create a `repo_root()` utility and a `repo_root` pytest fixture.
   - Use these to resolve the project root relative to the source/test file.
   - Pros: True machine independence.
   - Cons: Requires broad changes to test files.
   - Effort: Medium

2. **Placeholder Scrubbing**
   - Use a script to replace absolute paths in fixtures and documentation with a generic `<REPO_ROOT>` placeholder.
   - Pros: Cleaner repository state.
   - Cons: Might break tests that expect the real path string.
   - Effort: Medium

### Recommendation
Combine both approaches. Implement a dynamic `repo_root` fixture for all active code and tests. Use a placeholder for non-executable artifacts (docs/logs) to maintain a clean git history.

### Risks
- Some tests might perform strict string matching against output that includes the repository path. These must be updated to use relative paths or flexible matching.

### Ready for Proposal
Yes.
