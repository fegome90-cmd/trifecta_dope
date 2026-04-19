## Status: success
## Summary: Single clean commit (Decision A) for the skill-hub-corpus-integrity-guard feature. 12 source+test files are cohesive (domain evaluator, config model, write/read path integration) with 86/86 tests passing, mypy strict clean, and ruff clean. 38 pre-existing failures are unrelated.
## Artifacts: /tmp/fork-architect-triintplan.md
## Next: implementer
## Risks: 38 pre-existing test failures may confuse CI; committing to main (no feature branch) limits rollback granularity.
## Skill Resolution: injected

## Design Document

### Decision

**Decision A — single clean commit** for the integrity guard feature only.

Rationale:
1. The 10 source/test files form a single cohesive feature: domain evaluator (`skill_hub_corpus_integrity.py`), config model (`SkillHubIntegrityConfig`), write-path integration (`use_cases.py`), read-path transport (`context_service.py`), and 4 test files (86 tests total, all passing).
2. All modified tracked files contain **only** integrity-guard changes — no unrelated edits mixed in (verified via `git diff HEAD`).
3. The `.gitignore` change (adding `.fork/`) is directly related to the tooling used during development and is safe to bundle.
4. The 38 failing unit tests are **pre-existing** (documented in the handoff) and touch unrelated modules (LSP handler, CLI create naming, skill_hub runtime promotion, t7 verification). They are not caused by this change.
5. Excluding the `_ctx/` runtime artifacts, `docs/`, `scripts/`, `openspec/`, and other untracked files keeps the commit atomic and revertible.

### File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/domain/skill_hub_corpus_integrity.py` | add (234 lines) | Pure domain evaluator: corpus integrity check, verdict dataclass, receipt block |
| `src/domain/models.py` | modify | Add `SkillHubIntegrityConfig` + `TrifectaConfig.skill_hub_integrity` field |
| `src/domain/context_models.py` | modify | Add `SearchResult.authority_state` field with docstring |
| `src/application/use_cases.py` | modify | Integrity guard integration in promotion path: fail-closed config load, verdict forwarding, publication_state in receipt, `_publish()` state-aware |
| `src/application/context_service.py` | modify | `_load_pack()` returns `(pack, authority_state)` tuple; `_validate_and_load_promoted_set()` extracts publication_state; `search()` injects authority_state; blocked-is-inadmissible logic |
| `tests/unit/test_skill_hub_corpus_integrity.py` | add (589 lines) | Domain evaluator unit tests (40 tests) |
| `tests/unit/test_skill_hub_corpus_integrity_receipt.py` | add (595 lines) | Receipt + publication state integration tests (25 tests) |
| `tests/unit/test_authority_state_transport.py` | add (268 lines) | Read-path authority_state transport tests (7 tests) |
| `tests/unit/test_skill_hub_corpus_integrity_read_path.py` | add (~350 lines) | Extended read-path tests: fallback, legacy compat, blocked inadmissibility (14 tests) |
| `.gitignore` | modify | Add `.fork/` entry |

**Total: 5 modified + 5 new = 10 files**

### Files to Exclude / Defer

| File / Pattern | Reason |
|----------------|--------|
| `_ctx/context_pack.json` | Runtime artifact — regenerated on sync, not source code |
| `_ctx/telemetry/events.jsonl` | Telemetry log — auto-generated |
| `_ctx/telemetry/last_run.json` | Telemetry state — auto-generated |
| `_ctx/checklists/` | Checkpoint infrastructure, not this feature |
| `_ctx/handoffs/` | Checkpoint infrastructure |
| `_ctx/plans/` | Planning artifacts |
| `.kilocode/package-lock.json` | Unrelated tooling |
| `docs/audits/`, `docs/contracts/`, `docs/reports/`, `docs/skill-hub-*.md` | Documentation from prior exploration — separate commit |
| `openspec/` | OpenSpec scaffolding — separate commit |
| `scripts/skill_hub_cards.py`, `scripts/skill_hub_cards_core.py` | Separate feature (skill_hub_cards) — different scope |
| `tests/unit/test_skill_hub_cards_governed.py` | Tests for skill_hub_cards, not integrity guard |
| `tests/unit/test_skill_hub_cards_wrapper_contract.py` | Tests for skill_hub_cards wrapper |
| `.fork/` | Orchestration workspace — already gitignored |

### Acceptance Criteria

- [ ] All 86 integrity-guard tests pass: `uv run pytest tests/unit/test_skill_hub_corpus_integrity.py tests/unit/test_skill_hub_corpus_integrity_receipt.py tests/unit/test_authority_state_transport.py tests/unit/test_skill_hub_corpus_integrity_read_path.py -v`
- [ ] ruff clean on all 5 source files: `uv run ruff check src/domain/skill_hub_corpus_integrity.py src/domain/models.py src/domain/context_models.py src/application/use_cases.py src/application/context_service.py`
- [ ] mypy strict clean on all 5 source files: `uv run mypy src/domain/skill_hub_corpus_integrity.py src/domain/models.py src/domain/context_models.py src/application/use_cases.py src/application/context_service.py`
- [ ] No new test regressions introduced (the 38 pre-existing failures must remain the same set)
- [ ] Commit message follows conventional commits: `feat(domain): add skill-hub corpus integrity guard`
- [ ] Only the 10 files listed above are staged (verify with `git diff --cached --stat`)

### Rollback Plan

1. `git revert HEAD` — single commit reverts cleanly since all 10 files are atomic to this feature.
2. Alternatively: `git reset --soft HEAD~1` to unstage and re-edit if pre-push.
3. The `_ctx/` promoted set artifacts are not affected (no CLI or rendering changes in this commit).
4. No database migrations, no config file format changes (new fields have safe defaults).

### Risks

1. **Pre-existing failures (38 tests) may block CI** — These failures existed before this change and span LSP handler, build context pack, skill_hub runtime promotion, and t7 verification modules. They should be tracked separately and are NOT caused by this commit.
2. **Committing to main** — The handoff does not mention a feature branch. If CI gate is strict (all tests must pass), this commit will fail CI due to pre-existing failures. Mitigation: commit to a feature branch (`feat/skill-hub-corpus-integrity-guard`) first, then merge after confirming the 38 failures are pre-existing.
3. **Config schema evolution** — `TrifectaConfig` gains `skill_hub_integrity` with safe defaults (empty tuple). Existing configs without this field will deserialize correctly due to `default_factory`.
