# Next Agent Checklist — Batch 2D SSOT Design

> Workflow aid, not authority.

## Start Here
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/docs/adr/ADR-004-runtime-surface-ssot.md (**sole authority / anchor**)
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/skills/runtime-ssot-anchor/SKILL.md (re-anchor workflow under ADR-004; helper only)
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/docs/plans/2026-03-27-batch-2d-runtime-ssot-design-plan.md (derived only; loses to ADR-004 on conflict)
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/docs/reports/2026-03-27-runtime-surface-ssot-evidence.md (supporting evidence only)
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/_ctx/handoff/handoff_2026-03-27_batch-2d-runtime-manager-ssot-design.md (continuity only)
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/_ctx/checkpoints/2026-03-27/checkpoint_132457_batch-2d-runtime-manager-ssot-handoff.md (continuity only; pair with `$checkpoint-resume` only after re-anchor)
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/docs/plans/2026-03-26-lsp-daemon-followup-batches.md (historical reference only)
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/docs/reports/2026-03-26-daemon-drift-code-audit.md (missing in this worktree; verify location before relying on it)
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-batch-2d-runtime-manager/docs/reports/2026-03-26-lsp-daemon-comprehensive-review.md (missing in this worktree; verify location before relying on it)

## Guardrails
- Read `docs/adr/ADR-004-runtime-surface-ssot.md` first; it is the only allowed SSOT / anchor for this task
- Load `skills/runtime-ssot-anchor/SKILL.md` next to re-anchor the workflow under ADR-004
- Use `$checkpoint-resume` only as a continuity aid after that re-anchor
- No fallback authority: do not treat plan, report, handoff, checklist, checkpoint, or prior ADRs as co-equal authority
- Treat this as a design/SSOT follow-up, not a bugfix patch
- Stay in isolated worktree(s); do not pivot work back to dirty main
- If a derived artifact disagrees with `ADR-004`, stop and re-anchor instead of reconciling manually

## Recommended Order
- Read `ADR-004` first.
- Load the local `runtime-ssot-anchor` skill second.
- Use `$checkpoint-resume` only if continuity details are needed after the re-anchor.
- Read the derived plan/report/handoff/checkpoint only as subordinate context.
- Restate that the follow-up is limited to documentary realignment under `ADR-004`.
- Realign only the minimum subordinate artifacts needed; do not reopen artifact selection or invent a backup SSOT.
- Stop before any runtime code patch unless new evidence proves an active consumer and a real bugfix need.

## Current Status Snapshot
- Branch: codex/batch-2d-runtime-manager
- HEAD: d11d9f708dc06c4cf3e4b19d51b8a44556ae2a21
- Worktree status: clean
- Missing supporting paths to verify later: docs/reports/2026-03-26-daemon-drift-code-audit.md, docs/reports/2026-03-26-lsp-daemon-comprehensive-review.md

## Stop Conditions
- Stop if the work drifts into editing src/platform/runtime_manager.py or src/trifecta/platform/runtime_manager.py in this handoff follow-up.
- Stop if someone reframes code alignment as a bugfix without fresh consumer evidence.
- Stop if execution requires leaving isolated worktree(s) for dirty/divergent main.
