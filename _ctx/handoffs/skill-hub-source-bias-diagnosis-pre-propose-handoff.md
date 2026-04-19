# Checkpoint Handoff

Date: 2026-04-15 16:21:01 UTC
Branch: `codex/skill-hub-source-bias-investigation`
HEAD: `796b5a5039766e5fd928ef533504c8ec98109e12`

## What Changed

- Created isolated worktree `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/skill-hub-source-bias-investigation` on branch `codex/skill-hub-source-bias-investigation` from clean PR103 tip `796b5a50`.
- Reproduced the observed query skew: `security`, `worktree`, and `openai-docs` return only `pi-agent-skills`, while `codex` returns mixed `pi-agent-skills` and `codex-skills`.
- Confirmed the runtime authority for skill-hub search/cards is the promoted set under `~/.trifecta/segments/skills-hub/_ctx` (`skills_manifest.json`, `context_pack.json`, `skill_hub_promotion_receipt.json`) rather than `export_skills_catalog.py`.
- Verified historical evidence that the corpus used to be broad: 279 skills on 2026-03-06, 261 on 2026-03-19, and a 457-total-skills audit on 2026-03-19, all including claude/codex sources.
- Traced the collapse window to between 2026-03-19 and 2026-04-04, then identified the earliest confirmed collapsed promoted-set state sealed by a successful `ctx.sync` execution on 2026-04-12 10:37:46 -0400.
- Confirmed the real writer/reader chain: `src/application/use_cases.py` writes the promoted manifest/pack/receipt and seals `.skill_hub_last_valid`, while `src/application/context_service.py` reads live first and falls back to `.skill_hub_last_valid` if admission fails.
- Confirmed `scripts/export_skills_catalog.py` is offline export tooling and not part of the runtime promotion/build chain.

## Verified Evidence

- `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json` currently holds a 172-entry v1 manifest with sources `[pi-agent-skills, codex-skills]` and 171/1 skew.
- `~/.trifecta/segments/skills-hub/_ctx/.skill_hub_last_valid/skills_manifest.json` holds a 163-entry v2 manifest with 162/1 skew and matching sealed receipt/pack fingerprints.
- The earliest confirmed collapsed promoted set was sealed on 2026-04-12 10:37:46 -0400 / 2026-04-12T14:37:46.397496+00:00 during telemetry run `run_1776004666` (`ctx.sync`).
- Historical artifacts prove the corpus used to include broad multi-source coverage (claude/codex/agents/pi), so the current bias is a collapse/regression, not an original design.
- `scripts/export_skills_catalog.py` is not called by the runtime promotion/build chain.

## Remaining Blocker

- The exact shell wrapper/CLI string that invoked the 2026-04-12 `ctx.sync` writer event is still unproven; only the `ctx.sync` execution and resulting promoted-set write are confirmed.
- Current runtime corpus remains heavily collapsed/biased: current live manifest is 172 entries (171 `pi-agent-skills`, 1 `codex-skills`) and `.skill_hub_last_valid` is 163 entries (162 `pi-agent-skills`, 1 `codex-skills`).

## Next Agent

- Use $checkpoint-resume before doing any new work.
- Use $checkpoint-resume before any repo exploration or implementation.
- repo: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/skill-hub-source-bias-investigation
- checkpoint: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/skill-hub-source-bias-investigation/_ctx/checkpoints/2026-04-15/checkpoint_122101_skill-hub-source-bias-diagnosis-pre-propose.md
- supporting bundle: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/skill-hub-source-bias-investigation/{'workspace_bundle': ['/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/skill-hub-source-bias-investigation', '/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/docs/reports/skill-hub-source-bias-diagnosis-explore.md'], 'engram_topics': ['skill-hub/source-authority', 'discovery/skill-hub-corpus-collapse-window', 'discovery/skill-hub-collapsed-writer-event', 'preference/sdd-mode-skill-hub-source-investigation']}
- handoff: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/_ctx/handoffs/skill-hub-source-bias-diagnosis-pre-propose-handoff.md
- checklist: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/_ctx/checklists/skill-hub-source-bias-diagnosis-pre-propose-next-agent-checklist.md
Context loaded only. Waiting for your instruction.
- Use $checkpoint-resume before any repo exploration or implementation. Resume from the isolated worktree and start with `sdd-propose` for `skill-hub-source-bias-diagnosis`, using the confirmed `ctx.sync` writer event and promoted-set collapse evidence. Do not touch PR #103 branch/worktree during this new change. Context loaded only. Waiting for your instruction.
