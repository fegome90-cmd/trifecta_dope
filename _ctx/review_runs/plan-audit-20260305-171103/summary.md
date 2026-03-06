# tmux Plan Auditor v2

- **Session:** plan-audit
- **Run ID:** plan-audit-20260305-171103
- **Plan:** .pi/plan/trifecta-global-architecture.md
- **Run dir:** /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/_ctx/review_runs/plan-audit-20260305-171103
- **Timeout:** 300s
- **Auto-cleanup:** true

## Outputs

- [handoff.json](./handoff.json) - Main handoff file
- [patch-confirmation-template.json](./patch-confirmation-template.json) - User decisions template

## Agent outputs

- [agent-logic.json](./agent-logic.json)
- [agent-code-quality.json](./agent-code-quality.json)
- [agent-silent-failure.json](./agent-silent-failure.json)
- [agent-testing-static.json](./agent-testing-static.json)

## Manual attach

```bash
tmux attach -t plan-audit
```
