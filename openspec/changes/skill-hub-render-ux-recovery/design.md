# Design: Skill Hub Render UX Recovery

## Technical Approach

Recover the old first-impression feel by moving the banner + sentence-query guidance into repo-owned presentation code, while leaving semantic authority in the governed pipeline. `scripts/skill-hub` remains the public orchestration entrypoint, but it will stop calling `~/.local/bin/skill_hub_info_card.py` and instead render a repo-owned intro frame before delegating to the governed search/render flow. The classification boundary stays in `scripts/skill_hub_cards_core.py`; approved-card presentation stays in `src/cli/skill_cards.py`; fail-closed orchestration frames use `src/cli/error_cards.py`.

This change is filesystem-authored only in this parent runtime because Engram persistence is unavailable here; the OpenSpec files are the persistence source of truth for the phase.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Intro rendering home | Add a small governed intro helper in `src/cli/skill_cards.py` | Keep shell `echo` text in `scripts/skill-hub`; add a brand-new UX module | `skill_cards.py` already owns terminal presentation patterns, so the banner/guidance belongs with other approved card presentation, not in shell glue. |
| Error framing | Route unsupported/empty/runtime failures through `src/cli/error_cards.py` | Keep ad hoc stderr prose in `scripts/skill-hub` | Stable error cards are already the repo’s fail-closed pattern; reusing them preserves stream semantics and testability. |
| Authority split | Keep parse/normalize/classify in `scripts/skill_hub_cards_core.py` | Move classification into the wrapper or renderer | The core file already contains the governed planner and exit codes; UX recovery must not dilute that boundary. |
| Runtime dependency | Remove `~/.local/bin` from runtime behavior | Fall back to hidden-home helper when present | The change specifically restores UX without hidden authority; runtime must be self-contained in repo-owned sources. |

## Data Flow

```text
user query
   │
   ▼
scripts/skill-hub
   ├─ stdout: governed intro banner + sentence guidance
   ├─ search query / rerank
   └─ on failure → src/cli/error_cards.py → stderr
                │
                ▼
scripts/skill_hub_cards_core.py
   ├─ parse search output
   ├─ normalize + classify
   ├─ build render plan
   └─ exit codes: 0 / 1 / 3 / 4
                │
                ▼
src/cli/skill_cards.py
   └─ render approved cards only
```

## File Changes

| File | Action | Description |
|---|---|---|
| `scripts/skill-hub` | Modify | Emit governed intro/guidance, remove hidden-home helper call, preserve stdout/stderr and exit-code contract. |
| `scripts/skill_hub_cards_core.py` | Modify | Keep semantic authority intact; use governed error-card output for parse/runtime failures and keep classification semantics unchanged. |
| `src/cli/skill_cards.py` | Modify | Add a small intro/banner helper for the `skill-hub` first impression; keep approved-card rendering untouched. |
| `src/cli/error_cards.py` | Modify | Optionally add a skill-hub-specific wrapper/helper over `render_error_card(...)` so orchestration can emit stable failure cards without shell echo. |
| `tests/unit/test_skill_hub_cards_governed.py` | Modify | Cover intro/banner intent and ensure classification/rich/plain rendering stays unchanged. |
| `tests/unit/test_skill_hub_cards_wrapper_contract.py` | Modify | Assert no hidden-authority helper is invoked, stdout stays guidance-oriented, stderr carries governed error cards, and exit codes remain stable. |
| `tests/unit/test_skill_hub_runtime_promotion.py` | Modify | Extend contract checks so the promoted `skill-hub` wrapper still resolves only repo-owned runtime dependencies. |
| `docs/contracts/SKILL_HUB_CARDS_GOVERNED_CONTRACT.md` | Modify | Clarify that intro/guidance is presentation-only, governed, and never a semantic authority surface. |

## Interfaces / Contracts

```python
# src/cli/skill_cards.py
def render_skill_hub_intro(*, query_hint: str | None = None, file: IO[str] | None = None) -> None: ...

# src/cli/error_cards.py
def render_error_card(
    *,
    error_code: str,
    error_class: str,
    cause: str,
    next_steps: list[str],
    verify_cmd: str,
) -> str: ...
```

`scripts/skill-hub` will call the intro helper before normal search output. Any empty/unsupported/malformed path will emit a governed error card to stderr and return the existing non-zero code family; no success normalization is allowed.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Intro text shape, stream selection, and stable error-card payloads | Pure tests for the new intro helper and `render_error_card(...)` call sites. |
| Integration | Wrapper orchestration and exit codes | Subprocess tests for `scripts/skill-hub` covering success, empty query, parse/runtime failure, and legacy-helper absence. |
| E2E | Contract remains governed after promotion | Existing runtime-promotion tests plus one smoke that proves the promoted wrapper still has no `~/.local/bin` dependency. |

## Migration / Rollout

No migration required. This is a controlled UX recovery inside the governed runtime path.

## Open Questions

- None blocking. The only persistence caveat is the runtime Engram gap; filesystem OpenSpec artifacts are authoritative for this phase.
