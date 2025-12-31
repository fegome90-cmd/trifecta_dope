### Task 2: Define expected hits and pass criteria

**Files:**
- Create: `minirag-eval/specs/lsp_ast_positive.md`

**Step 1: Write the spec file**

```markdown
# LSP/AST Positive Spec

Goal: ensure LSP/AST queries retrieve relevant sources in top-5.

Expected sources (top-5):
- `docs/plans/2025-12-29-trifecta-context-loading.md`
- `docs/v2_roadmap/research_roi_matrix.md`
- `docs/research/agent_factory.md`
- `minirag-eval/bridges/all_bridges.md` (acceptable shortcut)

Pass criteria:
- 8/10 queries have at least one expected source in top-5.
```

**Step 2: Confirm file exists**

Run: `ls minirag-eval/specs/lsp_ast_positive.md`
Expected: file listed.

---
