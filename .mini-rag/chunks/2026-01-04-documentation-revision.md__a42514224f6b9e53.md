## Task 7: Run Final Validation

**Step 7.1: Sync and Validate**

```bash
uv run trifecta ctx sync -s .
uv run trifecta ctx validate -s .
```

**Step 7.2: Log Session**

```bash
uv run trifecta session append -s . --summary "Documentation revision complete for MVP" --files "README.md,skill.md,readme_tf.md,docs/"
```

---
