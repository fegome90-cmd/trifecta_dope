# LSP/AST Positive Eval Pack Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a positive retrieval test set focused on LSP/AST topics with explicit expected hits and runnable bench integration.

**Architecture:** Add a dedicated query file and spec in `minirag-eval/`, update summary logic to include the new module, and wire the module into the combined query list.

**Tech Stack:** Bash scripts, Python (standard library), Mini-RAG CLI.

---

### Task 1: Add LSP/AST positive query set

**Files:**
- Create: `minirag-eval/queries/lsp_ast_positive.txt`

**Step 1: Write the query file**

```
implementacion de ast tree-sitter
ast parser tree-sitter skeletonizer
que extraer del AST
implementacion de lsp symbols hover diagnostics
workspace symbols lsp search
lsp document symbols structure
lsp go to definition hover
lsp diagnostics hot files
fase 3 ast lsp ide grade fluidity
ast lsp hot files roadmap roi
```

**Step 2: Confirm file exists**

Run: `ls minirag-eval/queries/lsp_ast_positive.txt`
Expected: file listed.

---

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

### Task 3: Wire the new module into bench tooling

**Files:**
- Modify: `minirag-eval/summarize_results.py`
- Modify: `minirag-eval/README.md`
- Modify: `minirag-eval/queries/all.txt`

**Step 1: Extend `summarize_results.py`**

```python
results["lsp_ast_positive"] = parse_results(base / "lsp_ast_positive.md")

query_sets["lsp_ast_positive"] = [
    "implementacion de ast tree-sitter",
    "ast parser tree-sitter skeletonizer",
    "que extraer del AST",
    "implementacion de lsp symbols hover diagnostics",
    "workspace symbols lsp search",
    "lsp document symbols structure",
    "lsp go to definition hover",
    "lsp diagnostics hot files",
    "fase 3 ast lsp ide grade fluidity",
    "ast lsp hot files roadmap roi",
]

def lsp_ast_pass(query: str) -> bool:
    payload = results["lsp_ast_positive"].get(query, {})
    return any(
        s.endswith("2025-12-29-trifecta-context-loading.md")
        or s.endswith("research_roi_matrix.md")
        or s.endswith("agent_factory.md")
        or "all_bridges.md" in s
        for s in top_sources(payload)
    )

matchers["lsp_ast_positive"] = lsp_ast_pass
```

**Step 2: Update `minirag-eval/README.md`**

Add `lsp_ast_positive` to the module list and run examples.

**Step 3: Update `minirag-eval/queries/all.txt`**

Append the new 10 queries to the end of the file.

**Step 4: Run the module bench**

Run: `./minirag-eval/run_bench.sh lsp_ast_positive`
Expected: `minirag-eval/results/lsp_ast_positive.md` created.

**Step 5: Run summary**

Run: `python minirag-eval/summarize_results.py`
Expected: `lsp_ast_positive: 8/10 PASS` (or higher).

**Step 6: Commit**

```bash
git add minirag-eval/queries/lsp_ast_positive.txt \
  minirag-eval/specs/lsp_ast_positive.md \
  minirag-eval/summarize_results.py \
  minirag-eval/README.md \
  minirag-eval/queries/all.txt

git commit -m "test: add lsp/ast positive eval set"
```
