## Task 1: Update Root README.md

**Files:**
- Modify: `README.md`

**Step 1.1: Remove Dead References**

```bash
grep -n "braindope.md" README.md
# Expected: Line 338, 81 - REMOVE or update
```

**Step 1.2: Update Roadmap Section**

Replace the "Pending" section with actual status from Kanban:
- [x] Context Pack ✅
- [x] AST Symbols M1 ✅ (separate tool)
- [x] LSP Daemon ✅ (separate tool)
- [ ] Linter-Driven Loop (In Progress)

**Step 1.3: Remove Deprecated Script References**

```bash
grep -n "ingest_trifecta.py" README.md
# Remove or add stronger deprecation notice
```

**Step 1.4: Verify All Commands Work**

Run each documented command and verify output:
```bash
uv run trifecta --help
uv run trifecta ctx build --help
uv run trifecta ctx search --help
uv run trifecta ast symbols --help
```

**Step 1.5: Commit**

```bash
git add README.md
git commit -m "docs: update README with MVP status and remove dead refs"
```

---
