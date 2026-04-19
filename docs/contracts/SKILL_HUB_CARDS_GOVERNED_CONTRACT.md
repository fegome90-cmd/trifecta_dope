# Skill Hub Cards — Governed Runtime Contract

## Runtime SSOT

### Authoritative public surface
- `scripts/skill-hub`
- `scripts/skill-hub-cards`

`skill-hub --cards` MUST delegate only to `scripts/skill-hub-cards`.
`scripts/skill-hub-cards` is the only runtime authority for card classification and rendering.

### Presentation-only intro/guidance boundary
- Intro/banner and sentence-query guidance emitted by `scripts/skill-hub` are presentation-only UX framing.
- Intro/guidance text MUST NOT be treated as semantic/runtime authority for classification, promotion, or exit-code decisions.
- Semantic authority remains in the governed card pipeline (`scripts/skill-hub-cards` + governed core classifier flow).

### Deprecated surface
- `scripts/skill_hub_cards.py`

This Python entrypoint is deprecated as a rival surface. If kept temporarily, it MUST behave only as a shim delegating to the governed helper and MUST NOT contain parsing, classification, or rendering business rules of its own.

## Accepted raw input result types
- `repo`
- `skill`
- `session`
- `agent`
- `prime`

These are raw retrieval result types only. They are NOT final presentation semantics.

## Normalized kinds
- `renderable_skill`
- `metadata_only`
- `unsupported`
- `empty`

### Meaning
- `renderable_skill`: enough trusted fields exist to render a real skill card.
- `metadata_only`: administrative content exists, but it is not a usable skill card.
- `unsupported`: retrieval returned a non-empty hit that cannot be promoted safely to a skill card.
- `empty`: retrieval returned no hits at all.

## Promotion rule for raw `repo`
A raw `repo` hit MAY be promoted to `renderable_skill` only if the governed helper can reconstruct with sufficient confidence:
- stable id
- visible title
- readable path or trusted source/path combination
- useful description

Fail-closed rule:
- if confidence is insufficient, classify as `metadata_only` or `unsupported`
- NEVER invent a fake skill card from a weak `repo` hit

## Separation of concerns
The governed helper MUST separate these stages:
1. `parse_search_output(...)`
2. `normalize_result(...)`
3. `classify_result(...)`
4. `render_plain(...)`
5. `render_rich(...)`

Renderers present an already-classified outcome. They MUST NOT decide semantic kind.

## Exit code contract
| Outcome | Meaning | Exit code |
| --- | --- | --- |
| Renderable success | At least one `renderable_skill` card was rendered | `0` |
| Non-renderable, non-empty | Results exist but are only `metadata_only` and/or `unsupported` | `3` |
| Empty | Search returned no hits | `4` |
| Real execution/parse failure | Search/get/parsing/runtime error | `1` |

Notes:
- `metadata_only` MUST NOT reuse the empty exit code.
- `unsupported` shares the non-renderable exit family with `metadata_only`, but the emitted message MUST explain that the hit could not be safely promoted.

## Operational closure for promotion and verification
- The canonical receipt written by `skill-hub-runtime promote` enumerates only the public surfaces: `skill-hub` and `skill-hub-cards`.
- Operational support files required to execute those public surfaces may be synced during promotion, but they MUST NOT be promoted into new public surfaces or added to the canonical receipt.
- `skill-hub-runtime verify` MUST check both receipt integrity and minimal executable closure, including a stdin-driven smoke against the installed helper, so a missing private support file cannot still pass verification.

## Deprecated behaviors to remove
- deriving visible skill identity directly from `chunk_id.split(':')[1]`
- treating metadata-only results as `No skills found`
- keeping a second Python renderer entrypoint with divergent logic
- hiding classification rules inside the renderer

## Legacy helper policy (comparison-only)
- Legacy home-bin helpers (for example `~/.local/bin/skill_hub_info_card.py`) are NOT canonical runtime surfaces.
- They MAY be referenced only for historical comparison in tests/docs and MUST NOT participate in runtime execution paths.
