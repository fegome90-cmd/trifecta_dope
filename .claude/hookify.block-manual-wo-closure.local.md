---
name: block-manual-wo-closure
enabled: true
event: bash
action: block
pattern: git\s+(commit|merge).*wo-(close|done|finish|complete)
---

🚫 **Manual WO Closure Blocked**

You're attempting to manually commit a WO closure message. This bypasses the proper workflow validation.

**Why this matters:**
- Manual commits skip Definition of Done (DoD) validation
- Artifacts and closure documentation won't be generated
- WO state transitions won't be properly tracked
- Pre-commit hooks designed to catch issues are bypassed

**Correct workflow:**
```bash
# Use the proper finish script instead:
python scripts/ctx_wo_finish.py WO-XXXX

# This will:
# - Validate DoD requirements
# - Generate closure artifacts
# - Create proper commit with all metadata
# - Transition WO to done/ state
```

**If you need to bypass this rule:**
1. Set `enabled: false` in `.claude/hookify.block-manual-wo-closure.local.md`
2. Run with `--no-verify` flag (not recommended)
3. Make the commit, then run `ctx_wo_finish.py` to fix state

**Pre-commit hook reference:** Commit `f05a10f` - "feat(wo): add pre-commit hook to prevent manual WO closure"
