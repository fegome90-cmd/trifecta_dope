# Proposal: Remove Hardcoded Local Paths for Machine Independence

## Intent
Eliminate absolute local path references (pointing to `<REPO_ROOT>/`) to ensure the project is fully portable, CI-ready, and capable of running on any development machine without manual configuration.

## Scope

### In Scope
- **Dynamic Root Utility**: Implement a `repo_root()` helper in `src/domain/repo_ref.py` (or similar) that walks up from `__file__`.
- **Pytest Fixture**: Create a `repo_root` fixture in `tests/conftest.py` for global use in tests.
- **Test Refactoring**: Update all `skipif` conditions and `Path` arguments in `tests/` to use dynamic resolution.
- **Script Hardening**: Update shell scripts to use relative paths or environment variables like `TRIFECTA_CLI_ROOT`.
- **Artifact Scrubbing**: Replace absolute paths in documentation and log fixtures with a generic `<REPO_ROOT>` placeholder.

### Out of Scope
- Changing the structure of the `_ctx` directory or other core architectural paths.
- Modifying paths in binary files (e.g., `.pyc`).

## Capabilities

### New Capabilities
- `portable-testing`: Tests can be executed in any environment (Clean Machine, CI) without path-related skips.
- `environment-agnostic-docs`: Documentation and logs are clean and shareable without exposing local machine details.

## Approach
We will implement a dynamic resolution strategy. A central utility will identify the repository root by searching for `pyproject.toml`. Pytest will be configured with a global fixture to provide this root to all tests. We will then perform a surgical replacement of hardcoded strings in the codebase, followed by a mass-regex scrub of documentation and log fixtures.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `tests/conftest.py` | New | Global test configuration and fixtures. |
| `src/domain/repo_ref.py` | Modified | Add `repo_root()` utility. |
| `tests/acceptance/`, `tests/unit/` | Modified | Update skips and path arguments. |
| `scripts/*.sh` | Modified | Use dynamic path resolution. |
| `openspec/changes/`, `_ctx/logs/` | Modified | Scrub absolute paths. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Broken string matching in tests | Medium | Update test assertions to be relative-path aware or use globbing. |
| Nested repository confusion | Low | The root resolver will stop at the first `pyproject.toml` found while walking up. |

## Rollback Plan
Revert changes via git. The dynamic utility is additive and backward compatible if necessary.

## Success Criteria
- [ ] `grep -r "<REPO_ROOT>/"` returns no results in `src/`, `scripts/`, or `tests/`.
- [ ] All tests previously skipped due to path issues now execute and pass in a simulated clean environment.
- [ ] `trifecta doctor` reports a healthy state regardless of the repository's absolute location.
