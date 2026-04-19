# Exploration — skill-hub-default-path-origin-doctor

## Goal
Diagnose the operational/original source of the `skill-hub` bug without fixing it:
- `skill-hub "query"` does not show the banner/render
- `skill-hub "query" --cards` does not activate cards because parsing appears to depend on argument position

## Evidence read
### Files inspected
- `/Users/felipe_gonzalez/.local/bin/skill-hub`
- `/Users/felipe_gonzalez/.local/bin/skill-hub-cards`
- `/Users/felipe_gonzalez/.local/bin/skill-hub-runtime` (missing in this runtime)
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub`
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-cards`
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-runtime`
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_runtime_ux.py`
- Context files: `skill.md`, `_ctx/agent_trifecta_dope.md`, `_ctx/session_trifecta_dope.md`, `_ctx/prime_trifecta_dope.md`

### Behavioral probes
- `env UV_CACHE_DIR=/tmp/uvcache /Users/felipe_gonzalez/.local/bin/skill-hub "sql data base"`
  - Output: raw search results only, no intro/banner.
- `env UV_CACHE_DIR=/tmp/uvcache /Users/felipe_gonzalez/.local/bin/skill-hub "sql data base" --cards`
  - Output: raw search results only, no cards path.
- `env UV_CACHE_DIR=/tmp/uvcache /Users/felipe_gonzalez/.local/bin/skill-hub --cards "sql data base"`
  - Output: cards output, so the cards route is positional and only triggers when `--cards` is first.

## Findings

### 1) This is primarily a CLI parsing / flag-position bug
The installed wrapper at `/Users/felipe_gonzalez/.local/bin/skill-hub` uses a `while [ $# -gt 0 ]` parser and only enters cards mode if `--cards|-c` is seen during that loop. In theory it should accept flags anywhere, but the installed script is not the same as the repo script and its operational behavior is not aligned with the new runtime contract.

The repo script `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub` has already moved to a *positional-first* contract:
- `if [ "${1:-}" = "--cards" ]; then ...`
- then `QUERY="$*"`
This means `--cards` only works when it is the first argument, which matches the observed `skill-hub --cards "..."` success and `skill-hub "..." --cards` failure.

### 2) There is split-brain between installed binary and repo source
The installed `/Users/felipe_gonzalez/.local/bin/skill-hub` and the repo source `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub` are materially different:
- Installed binary: older parser, older help text, `--cards`/`--limit` option loop, card delegation via `uv run python "$TRIFECTA_ROOT/scripts/skill_hub_cards_core.py" ...`
- Repo script: newer runtime wrapper structure, no `--limit` option handling, positional `--cards` gate, intro/error rendering via `skill_hub_runtime_ux.py`, and rerank ref prefix updated from `skill:` to `repo:`

This is not just cosmetic drift — the two files encode different behavior and different authority assumptions.

### 3) The banner/render omission on default path is architecture/runtime drift, not just search output
The newer repo script explicitly tries to emit intro UX through `skill_hub_runtime_ux.emit_intro()` before cards mode, but the installed binary does not call that path. The installed binary jumps straight into search output with no intro banner in the default path. So the missing banner is an authority/runtime mismatch, not merely a rendering bug inside the search backend.

### 4) Runtime authority is incomplete / partially missing
`/Users/felipe_gonzalez/.local/bin/skill-hub-runtime` does not exist in this runtime, while the repo contains `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-runtime` plus `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_runtime_ux.py`.

That means the promoted/bin path set is incomplete relative to the repo contract. The promoted artifact set is not in sync with the source tree, which is consistent with runtime drift / split-brain authority.

### 5) The cards helper itself is present, but its invocation route differs
`/Users/felipe_gonzalez/.local/bin/skill-hub-cards` is a very thin wrapper that imports `skill_hub_cards_core.cli`. The repo’s `scripts/skill-hub` in the newer contract uses `skill_hub_runtime_ux.py` for intro/error cards and then delegates `--cards` handling to the helper. So the cards rendering piece exists, but the path to reach it depends on the script variant being invoked.

## Diagnosis summary
This bug is a **compound authority-flow problem** with two layers:

1. **Primary visible bug:** positional CLI parsing in the promoted runtime makes `--cards` only work when first, so `skill-hub "query" --cards` falls into the default search path.
2. **Deeper root cause:** the installed runtime under `~/.local/bin` is out of sync with the repo scripts and does not reflect the newer intro/cards authority model. There is drift between the promoted binary and the repo source of truth.

So the issue is not a single banner-render defect. It is a **split-brain between default-path and cards-path authority**, with the promoted wrapper/runtime not matching the repo’s current contract.

## What I did not do
- No code changes
- No fixes applied
- No tests/builds run

## Recommended next step
Move to a focused apply phase that either:
- reconciles the promoted `~/.local/bin/skill-hub` behavior with the repo contract, or
- restores a single authoritative parsing/UX contract and then repromotes the runtime artifacts.

