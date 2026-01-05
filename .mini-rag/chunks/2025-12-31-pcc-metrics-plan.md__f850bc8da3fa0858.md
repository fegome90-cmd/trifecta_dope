### Task 4: ADR for PCC metrics

**Files:**
- Create: `docs/adr/ADR_PCC_METRICS.md`

**Step 1: Draft ADR**

Include:
- Scope: PCC metrics for tool-calling (skill/prime/agent)
- Metrics definitions (path/tool/instruction correctness, false vs safe fallback, determinism)
- Data sources (dataset + eval-plan output + PRIME feature_map)
- Guardrails (tie->fallback, true_zero_guidance=0)

**Step 2: Commit**

```bash
git add docs/adr/ADR_PCC_METRICS.md
git commit -m "docs: add PCC metrics ADR"
```

---
