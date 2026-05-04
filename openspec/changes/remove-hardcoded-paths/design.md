# Design: Remove Hardcoded Local Paths

## Technical Approach
The strategy consists of three main components:
1. **Dynamic Root Resolution**: Implementing a central utility to find the repository root relative to the execution context.
2. **Test Infrastructure Agnosticism**: Updating all test modules to use the dynamic root instead of hardcoded strings, ensuring portability.
3. **Artifact Anonymization**: Scrubbing machine-specific paths from documentation and log fixtures to maintain a clean, shareable state.

## Architecture Decisions

### Decision: Centralize Root Resolution in Domain
**Choice**: Implement `get_repo_root()` in `src/domain/segment_resolver.py`.
**Alternatives considered**: Hardcoding relative paths in each test, using environment variables only.
**Rationale**: Centralizing the logic ensures consistency across CLI, daemon, and tests. Walking up to find `pyproject.toml` is the most robust way to identify the repo boundary.

### Decision: Global Pytest Fixture for Tests
**Choice**: Create a `repo_root` fixture in `tests/conftest.py`.
**Rationale**: Avoids redundant root resolution logic in every test file. Fixtures are the idiomatic way to provide shared context in Pytest.

### Decision: Placeholder Scrubbing for Non-Code Artifacts
**Choice**: Use `<REPO_ROOT>` and `<HOME>` placeholders in Markdown and JSON logs.
**Rationale**: Documentation and logs should reflect the structure, not the specific machine. Placeholders keep the git history clean and prevent "leaks" of personal directory structures.

## Data Flow
The system resolves its root at startup (for CLI) or during test setup (via fixture).

    [CLI/Test] ──→ [segment_resolver.get_repo_root()] ──→ [Walk up to pyproject.toml]
                                                                  │
                                                                  ▼
    [Dynamic Path] ←────────────────────────────────────────── [Result]

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/domain/segment_resolver.py` | Modify | Add `get_repo_root()` and `get_home_path()` utilities. |
| `tests/conftest.py` | Create | Define global `repo_root` and `fake_home` fixtures. |
| `tests/acceptance/test_harness_blackbox.py` | Modify | Use `repo_root` in `skipif` and `cwd`. |
| `tests/unit/test_pd_regression.py` | Modify | Replace hardcoded `Path` with dynamic resolution. |
| `tests/unit/test_skill_hub_cards_governed.py` | Modify | Use relative paths for skill fixtures. |
| `scripts/scrub_paths.py` | Create | Script to mass-replace local paths with placeholders in artifacts. |

## Interfaces / Contracts

```python
# src/domain/segment_resolver.py

def get_repo_root() -> Path:
    """Finds repo root by searching for pyproject.toml."""
    # ... logic ...

def get_home_path() -> Path:
    """Returns Path.home() but allows override via environment variable."""
    # ... logic ...
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Root Resolver | Test `get_repo_root()` returns correct path in different directory depths. |
| Acceptance | Portable Run | Run `pytest tests/acceptance` from a different parent directory to verify no skips occur. |
| Integration | Scrubbing | Verify `scripts/scrub_paths.py` correctly replaces paths in a sample log file. |

## Migration / Rollout
1. Implement the utilities and fixtures.
2. Run a "find and replace" session across the `tests/` directory.
3. Run `scripts/scrub_paths.py` on all `openspec/` and `_ctx/logs/` files.
4. Verify all tests pass and `grep` returns no machine-specific paths.

## Open Questions
- [ ] Should we also redact the username "felipe_gonzalez" globally? (Decision: Yes, using `<USER>` placeholder).
