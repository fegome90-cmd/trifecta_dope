# Next Agent Checklist

## Start Here
- <REPO_ROOT>/Developer/agent_h/trifecta_dope/skill.md
- <REPO_ROOT>/Developer/agent_h/trifecta_dope/_ctx/agent_trifecta_dope.md
- <REPO_ROOT>/Developer/agent_h/trifecta_dope/_ctx/session_trifecta_dope.md
- <REPO_ROOT>/Developer/agent_h/trifecta_dope/_ctx/prime_trifecta_dope.md
- <REPO_ROOT>/Developer/agent_h/trifecta_dope/_ctx/checkpoints/2026-04-14/checkpoint_111756_pr103-post-review-autofix-audit.md
- <REPO_ROOT>/Developer/agent_h/trifecta_dope/_ctx/handoffs/pr103-post-review-autofix-audit-handoff.md
- <REPO_ROOT>/Developer/agent_h/trifecta_dope/_ctx/checklists/pr103-post-review-autofix-audit-next-agent-checklist.md

## Guardrails
- Use skill-hub or superpowers discipline during each material step
- Never build intentionally after changes
- Verify each review finding against current code and only fix or resolve what truly applies
- Do not resolve the three daemon-runtime bundle-tracked.patch threads unless the underlying daemon/runtime changes are actually accepted

## Recommended Order
- Read the checkpoint and handoff only.
- Verify the active blocker with fresh evidence.
- Continue on the narrowest remaining path.

## Current Status Snapshot
- {'branch': 'codex/skill-hub-ssot-rebuild', 'head': '4ce1df39481c61521731d29b776bcc2f6bd1288c', 'upstream': 'origin/codex/skill-hub-ssot-rebuild', 'upstream_head': '5265cce0d905bdeef1c853086b3fdd3900820c53', 'workspace_root': '<REPO_ROOT>/Developer/agent_h/trifecta_dope/.worktrees/skill-hub-ssot-rebuild', 'canonical_ssot': '<REPO_ROOT>/Developer/agent_h/trifecta_dope/openspec/specs/skill-hub-authority/spec.md'}

## Stop Conditions
- Stop if the next step reopens an out-of-scope front.
- Stop if the only path forward requires unsafe manual state changes.
