## Task 4: Verify and Update _ctx Files

**Files:**
- Modify: `_ctx/prime_trifecta_dope.md`
- Modify: `_ctx/agent_trifecta_dope.md`

**Step 4.1: Validate Prime Paths**

```bash
# Check that all paths in prime exist
for path in $(grep -E "^\d+\." _ctx/prime_trifecta_dope.md | sed 's/.*`\(.*\)`.*/\1/'); do
  test -f "$path" || echo "MISSING: $path"
done
```

**Step 4.2: Update Agent Gates Table**

Verify all gate commands in agent.md work:
```bash
uv run pytest tests/unit/ -v --collect-only
uv run trifecta ctx validate --segment .
```

**Step 4.3: Update Dates**

Update `last_verified` in agent.md frontmatter to `2026-01-04`.

**Step 4.4: Commit**

```bash
git add _ctx/
git commit -m "docs: verify and update _ctx files for 2026-01-04"
```

---
