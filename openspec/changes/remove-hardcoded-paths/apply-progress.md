# Implementation Progress: Remove Hardcoded Local Paths

## Mode: Strict TDD

### Completed Tasks
- [x] 1.1 Implement `get_repo_root()` and `get_home_path()` in `src/domain/segment_resolver.py`.
- [x] 1.2 Create `tests/conftest.py` with a global `repo_root` fixture.
- [x] 1.3 Add a `fake_home` fixture to `tests/conftest.py`.
- [x] 2.1 Refactor `tests/acceptance/test_harness_blackbox.py`.
- [x] 2.2 Refactor `tests/acceptance/test_pd_evidence_stop_e2e.py`.
- [x] 2.3 Refactor `tests/unit/test_pd_regression.py`.
- [x] 2.4 Refactor skill hub tests.
- [x] 2.5 Update tripwire tests.
- [x] 2.6 Update demo script.
- [x] 3.1 Create `scripts/scrub_paths.py`.
- [x] 3.2 Scrub documentation.
- [x] 3.3 Scrub logs.
- [x] 4.1-4.4 Verification.

### Files Changed
| File | Action | What Was Done |
|------|--------|---------------|
| `src/domain/segment_resolver.py` | Modified | Added dynamic root and home resolution. |
| `tests/conftest.py` | Created | Global fixtures for portability. |
| `tests/**/*.py` | Modified | Refactored to use dynamic paths. |
| `scripts/scrub_paths.py` | Created | Mass path redaction utility. |
| Multiple artifacts | Modified | Scrubbed absolute paths. |

### Deviations from Design
None — implementation matches design. Use of mass `sed` was more efficient for Phase 3 than individual file edits.

### Issues Found
- Pre-existing `ImportError` in `cli.py` entry point was fixed to enable test execution.
- Discovered hardcoded paths in hidden directories like `.mini-rag/` and scrubbed them.

### Status
16/16 tasks complete. Ready for final verification and archive.
