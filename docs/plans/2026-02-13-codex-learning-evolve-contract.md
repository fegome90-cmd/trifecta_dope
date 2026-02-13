# Codex Learning + Evolve Contract (v1)

## Functional Goals
1. Capture observation events from an official-first source (`codex exec --json`).
2. Convert repeated high-signal patterns into atomic instincts.
3. Manage instinct lifecycle with deterministic CLI operations.
4. Evolve related instincts into stronger reusable artifacts.

## Non-Goals (v1)
1. No default LLM-driven extraction.
2. No dependency on undocumented hook APIs.
3. No auto-promotion of evolved artifacts to curated skills without review.

## Privacy Rules
1. Observation logs remain local.
2. Export includes instincts only.
3. Raw observations are excluded from default export.

## Parity Map (ECC -> Codex)
| Capability | ECC | Codex v1 Target | Status |
|---|---|---|---|
| Plan-before-code | `/plan` | AGENTS policy + planning workflow | Now |
| Pattern capture | `/learn` | learned-skill generation protocol | Now |
| Instinct lifecycle | v2 instinct CLI | deterministic local CLI | Now |
| Evolve clustering | `/evolve` | `instinct_cli.py evolve` | Now |
| Hook capture | Pre/Post hooks | optional adapter only | Later/Optional |
| Background LLM observer | haiku loop | feature-flag, default off | Later |

## Acceptance Criteria
1. `ingest` normalizes JSONL from `codex exec --json` into observations.
2. `status/import/export/evolve` run end-to-end deterministically.
3. Rules-first observer generates instincts from:
   - repeated workflows
   - error-to-fix sequences
   - tool preference signals
4. Observer run archives processed observations and preserves fresh active log.

## Defaults
1. Canonical event source: `codex exec --json`.
2. Storage primary root: `~/.codex/homunculus`.
3. Compatibility root: `~/.agents/homunculus`.
4. Observer mode: `rules`.
5. `llm_enabled`: `false`.
