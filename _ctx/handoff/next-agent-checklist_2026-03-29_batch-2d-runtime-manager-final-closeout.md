# Next Agent Checklist — Batch 2D Final Closeout

## Start Here
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/docs/adr/ADR-004-runtime-surface-ssot.md` — only SSOT / authority.
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/skills/runtime-ssot-anchor/SKILL.md` — helper-only re-entry guide subordinate to ADR-004.
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/_ctx/checkpoints/2026-03-29/checkpoint_140437_batch-2d-runtime-manager-final-closeout.md` — checkpoint for this final bundle.
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/_ctx/handoff/handoff_2026-03-29_batch-2d-runtime-manager-final-closeout.md` — handoff for this final bundle.
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/_ctx/handoff/next-agent-checklist_2026-03-29_batch-2d-runtime-manager-final-closeout.md` — this checklist.

## Required Order
1. Read ADR-004 first.
2. Load `runtime-ssot-anchor` second.
3. Use `$checkpoint-resume` with the three explicit bundle files above.
4. Stop unless the user asks for docs/context-hygiene follow-up.

## Current Status Snapshot
- Branch: `codex/batch-2d-runtime-manager`
- HEAD: `d11d9f708dc06c4cf3e4b19d51b8a44556ae2a21`
- Canonical local segment identity: `trifecta_dope` via `_ctx/trifecta_config.json`
- Latest `ctx sync`: PASS
- `skill.md` duplicate warning: triaged / acceptable / no immediate action
- Large context-pack warning: optional docs/context-hygiene follow-up only (~5.08M chars / 5,075,961 chars)
- Runtime scope: closed; runtime code untouched

## Guardrails
- ADR-004 remains the only SSOT.
- Treat checkpoint/handoff/checklist as workflow aids, not authority.
- Ignore unrelated dirt and other agents' changes.
- Keep any remaining work out of `src/` unless fresh active-consumer evidence appears.

## Stop Conditions
- Stop if a derived artifact is being treated as co-equal with ADR-004.
- Stop if the task drifts into runtime implementation or runtime-manager edits.
- Stop if the only remaining question is the large context-pack warning and the user has not asked for docs/context-hygiene follow-up.
