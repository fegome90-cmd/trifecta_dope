---
name: block-session-bloat
enabled: true
event: bash
pattern: echo.*>>\s+.*session\.md
---

⚠️ **Session.md bloat detected!**

You're appending content to `session.md` without validation.

**Why this matters:**
- We just cleaned up 1801 empty debriefing templates from this exact pattern
- Unconditional appends cause massive file bloat
- Empty templates make the file nearly useless for context

**Before proceeding, verify:**
1. Is this content actually meaningful (not empty templates)?
2. Should this go through elle-sync or a proper update mechanism instead?
3. Are you appending to the RIGHT file?

**Better alternatives:**
- Use `/elle-sync` for structured context updates
- Add content through proper context management
- Check existing content first: `grep -c "###.*Debriefing" ~/.claude/.context/core/session.md`

**If you're sure:**
Use a more specific pattern or confirm with user first.
