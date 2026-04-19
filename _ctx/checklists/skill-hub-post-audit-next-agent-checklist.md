# Next Agent Checklist

## Start Here
- Use $checkpoint-resume before repo exploration.
- Read the generated checkpoint, handoff, and checklist only.
- Verify git status before staging anything.

## Guardrails
- Do not touch T7, daemon/LSP, wo_verify.sh, or unrelated dirt.
- Never build after changes.
- Keep one authority per skill-hub surface; do not reintroduce rival helper implementations.
- Use fresh verification evidence before any completion claim or publish step.

## Recommended Order
- Open the checkpoint via $checkpoint-resume.
- Inspect git status and isolate the intentional skill-hub slice.
- Stage or publish only if the user asks for that next step.

## Current Status Snapshot
- Branch: codex/skill-hub-authority-anchor-closeout
- HEAD: abb02938d602f40c789809415e85d451cca092d6
- Intentional modified files: scripts/skill-hub, scripts/skill-hub-cards, src/domain/skill_manifest.py, tests/unit/test_skill_hub_authority_phase_a.py
- Intentional untracked validation files: scripts/skill_hub_cards.py, scripts/skill_hub_cards_core.py, tests/unit/test_skill_hub_cards_governed.py, tests/unit/test_skill_hub_cards_wrapper_contract.py

## Stop Conditions
- Stop if the next step would reopen T7, daemon/LSP, or broad repo cleanup.
- Stop if publishing requires staging unrelated telemetry or workspace dirt.
