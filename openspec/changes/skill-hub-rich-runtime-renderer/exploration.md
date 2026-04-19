# Exploration: skill-hub rich runtime renderer

## Intent
Recover the beautiful rich skill-card rendering inside the governed promoted runtime, not only in repo-side reference modules.

## Skills used for this exploration
Discovered with `skill-hub`:
- `$sdd-explore`
- `$sdd-propose`
- `$sdd-design`
- `$sdd-tasks`
- `$python-cli-patterns`

Also applied because it is directly relevant even though current hub indexing did not surface it in search:
- `$authority-flow-audit`

## Current state
- The governed promoted runtime now owns intro, banner, and error framing in:
  - `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_runtime_ux.py`
- The governed runtime semantic authority still lives in:
  - `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_cards_core.py`
- But runtime card output still imports only plain helpers:
  - `render_cards_plain`
  - `render_non_renderable_message`
- The richer visual renderer still lives repo-side only in:
  - `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/src/cli/skill_cards.py`

## Problem framing
This is no longer a drift bug. The runtime is promoted correctly, but its presentation surface is intentionally narrower than the legacy or repo-side rich UX.

That creates a product gap:
- banner hero is back,
- cards still render plain,
- the full visual hierarchy the user remembers is missing.

## Authority-flow diagnosis
### Genuine authority today
- Query admission, normalization, classification, exit codes:
  - `scripts/skill_hub_cards_core.py`
- Runtime intro/error presentation:
  - `scripts/skill_hub_runtime_ux.py`
- Promotion and installed runtime completeness:
  - `scripts/skill-hub-runtime`

### Non-authoritative reference surface
- `src/cli/skill_cards.py`
- `src/cli/error_cards.py`

Those repo-side modules are useful references, but they are not safe to treat as promoted runtime authority.

## Approaches considered

### Option A — Port the rich card renderer into governed runtime code
Create runtime-owned rich/compact/plain renderers under `scripts/`, reusing design intent from `src/cli/skill_cards.py` but keeping production authority in promoted artifacts.

**Pros**
- restores the beautiful UX where users actually run the command
- preserves the current authority split
- keeps promoted runtime self-contained

**Cons**
- some duplication/refactoring work
- requires new runtime tests and promotion checks

### Option B — Keep runtime plain and only improve typography a little
Make plain rendering slightly nicer but avoid full panel rendering.

**Pros**
- smaller implementation
- lower dependency/compat risk

**Cons**
- does not satisfy the product expectation of the rich renderer
- likely leads to another UX dissatisfaction cycle

### Option C — Reuse `src/cli/skill_cards.py` directly from runtime
Have the promoted runtime import repo-side renderer modules again.

**Pros**
- less code movement at first glance

**Cons**
- reopens the exact authority/runtime coupling we just removed
- fragile for promotion and installed runtime completeness
- architecturally wrong

## Recommendation
Choose **Option A**.

Port the rich runtime renderer into governed `scripts/` code, probably by expanding `scripts/skill_hub_runtime_ux.py` or adding an adjacent runtime-owned renderer module under `scripts/`, then make `scripts/skill_hub_cards_core.py` choose `rich` for TTY and `plain` for non-TTY while preserving semantic authority and fail-closed behavior.

## Likely affected files
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_runtime_ux.py`
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_cards_core.py`
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-cards`
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-runtime`
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_skill_hub_cards_governed.py`
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_skill_hub_render_parity.py`
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_skill_hub_runtime_promotion.py`

## Risks to control
- rich runtime renderer must not take semantic ownership away from `skill_hub_cards_core.py`
- runtime must remain self-contained after promotion
- TTY-only rich rendering must still degrade cleanly to plain for pipes/agents
- no hidden dependency on `src/cli/*`
