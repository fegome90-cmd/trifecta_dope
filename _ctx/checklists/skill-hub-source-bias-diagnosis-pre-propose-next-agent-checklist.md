# Next Agent Checklist

## Start Here
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/skill.md
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/_ctx/agent_trifecta_dope.md
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/_ctx/session_trifecta_dope.md
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/_ctx/prime_trifecta_dope.md
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/docs/adr/ADR-004-skill-hub-runtime-promotion-policy.md
- /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/docs/reports/skill-hub-source-bias-diagnosis-explore.md
- Engram topic: skill-hub/source-authority
- Engram topic: discovery/skill-hub-corpus-collapse-window
- Engram topic: discovery/skill-hub-collapsed-writer-event

## Guardrails
- Interactive mode, hybrid artifacts.
- Never build after changes.
- Stay in `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/skill-hub-source-bias-investigation` for this new change.
- Treat PR #103 cleanup work as closed; do not reopen or contaminate `codex/skill-hub-ssot-rebuild`.
- Do not treat `export_skills_catalog.py` as runtime authority unless new evidence disproves the current forensics.

## Recommended Order
- Read the checkpoint and handoff only.
- Verify the active blocker with fresh evidence.
- Continue on the narrowest remaining path.

## Current Status Snapshot
- {'repo': '/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/skill-hub-source-bias-investigation', 'branch': 'codex/skill-hub-source-bias-investigation', 'head': '796b5a5039766e5fd928ef533504c8ec98109e12', 'next_sdd_phase': 'sdd-propose', 'artifact_store': 'hybrid', 'execution_mode': 'interactive'}

## Stop Conditions
- Stop if the next step reopens an out-of-scope front.
- Stop if the only path forward requires unsafe manual state changes.
