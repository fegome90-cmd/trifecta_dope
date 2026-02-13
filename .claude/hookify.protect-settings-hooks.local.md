---
name: protect-settings-hooks
enabled: true
event: file
conditions:
  - field: file_path
    operator: ends_with
    pattern: settings.json
  - field: new_text
    operator: contains
    pattern: SessionEnd|PreToolUse|PostToolUse|SessionStart
---

⚠️ **Editing hooks in settings.json!**

You're modifying hook configurations directly.

**Why this matters:**
- Broken hooks can cause silent failures or unexpected behavior
- The empty debriefing template issue came from a SessionEnd hook
- Hook changes affect EVERY Claude Code session

**Before committing this edit:**
1. **Test the hook** - Does it execute without errors?
2. **Verify the pattern** - Will it match what you expect?
3. **Check side effects** - What else does this affect?

**Common hook issues:**
- Unconditional execution (like our debriefing template problem)
- Missing error handling (scripts that fail silently)
- Expensive operations (hooks that slow down every tool use)
- Resource conflicts (multiple hooks modifying same files)

**If adding a new hook:**
- Start with `enabled: false` for testing
- Test in isolation before combining with other hooks
- Document what the hook does in comments

**If modifying an existing hook:**
- Understand why it exists before changing
- Check if other tools/systems depend on it
- Consider if a parameter/flag would be better than a hard change
