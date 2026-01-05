## Task 5: Archive Old Session Entries

**Files:**
- Modify: `_ctx/session_trifecta_dope.md`
- Create: `docs/evidence/session_archive_2025.md`

**Step 5.1: Archive 2025 Entries**

Move all entries before 2026-01-01 to archive file.

**Step 5.2: Keep Recent Entries**

Keep only entries from 2026-01-01 onwards in active session file.

**Step 5.3: Add Archive Reference**

Add note at top of session.md:
```markdown
> For entries before 2026-01-01, see [archive](../docs/evidence/session_archive_2025.md)
```

**Step 5.4: Commit**

```bash
git add _ctx/session_trifecta_dope.md docs/evidence/
git commit -m "docs: archive 2025 session entries"
```

---
