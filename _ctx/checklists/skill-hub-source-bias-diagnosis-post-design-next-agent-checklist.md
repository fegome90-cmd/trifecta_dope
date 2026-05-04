# Next Agent Checklist

## Start Here
- <REPO_ROOT>/Developer/agent_h/trifecta_dope/skill.md
- <REPO_ROOT>/Developer/agent_h/trifecta_dope/_ctx/agent_trifecta_dope.md
- <REPO_ROOT>/Developer/agent_h/trifecta_dope/_ctx/session_trifecta_dope.md
- <REPO_ROOT>/Developer/agent_h/trifecta_dope/_ctx/prime_trifecta_dope.md
- <REPO_ROOT>/Developer/agent_h/trifecta_dope/docs/adr/ADR-004-skill-hub-runtime-promotion-policy.md
- <REPO_ROOT>/Developer/agent_h/trifecta_dope/docs/reports/skill-hub-source-bias-diagnosis-explore.md

## Guardrails
- Interactive SDD flow; stop after each phase for user review.
- Artifact store is Engram only for this resumed session.
- Stay inside the isolated worktree and do not contaminate PR #103 or `codex/skill-hub-ssot-rebuild`.
- Never build after changes.
- Do not treat `export_skills_catalog.py` as runtime authority unless new evidence disproves the current forensics.

## Recommended Order
- Read the checkpoint and handoff only.
- Verify the active blocker with fresh evidence.
- Continue on the narrowest remaining path.

## Current Status Snapshot
- {'repo': '<REPO_ROOT>/Developer/agent_h/trifecta_dope/.worktrees/skill-hub-source-bias-investigation', 'branch': 'codex/skill-hub-source-bias-investigation', 'head': '796b5a5039766e5fd928ef533504c8ec98109e12', 'next_sdd_phase': 'sdd-tasks', 'artifact_store': 'engram', 'execution_mode': 'interactive', 'workspace_bundle': ['<REPO_ROOT>/Developer/agent_h/trifecta_dope/.worktrees/skill-hub-source-bias-investigation', '<REPO_ROOT>/Developer/agent_h/trifecta_dope/docs/reports/skill-hub-source-bias-diagnosis-explore.md']}

## Stop Conditions
- Stop if the next step reopens an out-of-scope front.
- Stop if the only path forward requires unsafe manual state changes.
