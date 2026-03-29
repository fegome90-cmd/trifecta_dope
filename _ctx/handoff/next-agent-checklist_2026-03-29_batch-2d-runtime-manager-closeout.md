# Next Agent Checklist — Batch 2D Closeout

## Start Here
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/docs/adr/ADR-004-runtime-surface-ssot.md — sole SSOT / authority.
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/skills/runtime-ssot-anchor/SKILL.md — helper-only re-entry bridge, subordinate to ADR-004.
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/_ctx/checkpoints/2026-03-29/checkpoint_113545_batch-2d-runtime-manager-closeout.md — generated checkpoint for this closeout bundle (workflow aid, not authority).
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/_ctx/handoff/handoff_2026-03-29_batch-2d-runtime-manager-closeout.md — generated handoff for this closeout bundle (workflow aid, not authority).
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/_ctx/handoff/next-agent-checklist_2026-03-29_batch-2d-runtime-manager-closeout.md — generated checklist for this closeout bundle (workflow aid, not authority).
- After re-anchoring on ADR-004, use $checkpoint-resume with the three explicit bundle files above only as continuity aids.
## Guardrails
- ADR-004 remains the only SSOT / authority for Batch 2D.
- Treat checkpoint, handoff, checklist, plan, and report artifacts as workflow aids, not authority.
- Do not patch runtime code or reopen runtime-manager work in this closeout follow-up.
- Stay inside /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager and ignore unrelated changes elsewhere.

## Recommended Order
- Re-anchor on ADR-004 first.
- Load the local runtime-ssot-anchor skill second.
- Use the generated checkpoint/handoff/checklist bundle only after that re-anchor.
- Make a triage/decision call on the two ctx-sync warnings only if more work is requested.
- Stop before any runtime implementation work.

## Current Status Snapshot
- Branch: codex/batch-2d-runtime-manager
- HEAD: d11d9f708dc06c4cf3e4b19d51b8a44556ae2a21
- Canonical local segment identity: trifecta_dope (_ctx/trifecta_config.json)
- Latest ctx sync: PASS
- Remaining warnings: duplicate skill.md cycle warning; large context pack warning (~5.08M chars / 5,075,961 chars)
- Runtime code status for this step: untouched / out of scope

## Stop Conditions
- Stop if follow-up drifts into src/platform/runtime_manager.py or src/trifecta/platform/runtime_manager.py edits.
- Stop if any derived artifact is treated as co-equal authority with ADR-004.
- Stop if warning triage is being reframed as runtime bugfix work without fresh consumer evidence.
