### Task 6: Operational docs + usage contract

**Files:**
- Create: `docs/ops/claude-code-wrapper.md`
- Modify: `README.md`
- Modify: `readme_tf.md`

**Step 1: Write doc changes**

```md
# Claude Code Wrapper
- Install: ln -s $(pwd)/bin/cc ~/.local/bin/cc
- Usage: cc <claude args>
- Guarantees: session update + ctx sync/validate + fail-closed
```

**Step 2: Verify docs render**

Run: `rg -n "cc " README.md readme_tf.md docs/ops/claude-code-wrapper.md`
Expected: references to wrapper and guarantees.

**Step 3: Commit**

```bash
git add docs/ops/claude-code-wrapper.md README.md readme_tf.md
git commit -m "docs: add claude wrapper runbook"
```

---
