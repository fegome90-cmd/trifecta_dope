# Codex Learning + Evolve Contract (v1)

## Functional Goals
1. Capture observation events from official Codex-compatible source (`codex exec --json`).
2. Convert patterns into atomic instincts with confidence.
3. Manage lifecycle via deterministic CLI (`status/import/export/evolve/ingest`).
4. Evolve related instincts into stronger reusable artifacts.

## Non-Goals (v1)
- No default LLM-driven extraction.
- No dependency on undocumented hook APIs.
- No automatic promotion of evolved artifacts into production skills.

## Privacy Rules
- Observation logs stay local.
- Export includes instincts only.
- Raw observations are never exported by default.

## Parity Table (ECC -> Codex)
| Capability | ECC | Codex v1 target | Status |
|---|---|---|---|
| Plan-before-code | `/plan` command | AGENTS policy + plan workflow | Now |
| Mid/late learning capture | `/learn` | learned skill creation protocol | Now |
| Instinct lifecycle | v2 instinct CLI | deterministic local CLI | Now |
| Evolve clustering | `/evolve` | `instinct_cli.py evolve` | Now |
| Hook capture | Pre/Post hooks | optional adapter only | Later/Optional |
| LLM observer | background haiku flow | feature-flag, default off | Later |

## Acceptance Criteria
1. `ingest` processes `codex exec --json` JSONL into normalized observations.
2. `status/import/export/evolve` run end-to-end with deterministic outputs.
3. `rules_observer.py` generates instincts from repeated workflows/error-fix/tool preference signals.
4. `start_observer.sh run-once` creates/updates instincts and archives processed observations.
