## DEPLOYMENT CHECKLIST

- [ ] All PRs merged to main (T1 → T2 → T3 → T4)
- [ ] CHANGELOG.md updated with "Telemetry: AST/LSP instrumentation"
- [ ] docs/telemetry.md created/updated with:
  - [ ] Specification of new event types (ast.parse, lsp.spawn, etc.)
  - [ ] Example queries for metrics
  - [ ] "READY" definition for LSP
  - [ ] Redaction policy (no absolute paths, no content)
- [ ] Example data generated: run ctx.search/ctx.get, collect _ctx/telemetry/*
- [ ] Share sanitized example events.jsonl + last_run.json in PR description

---
