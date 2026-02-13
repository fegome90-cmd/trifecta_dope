---
name: warn-context-echo
enabled: true
event: bash
conditions:
  - field: command
    operator: contains
    pattern: echo >>
  - field: command
    operator: regex_match
    pattern: (\.claude/\.context/|session\.md|journal\.md|identity\.md|preferences\.md|rules\.md|workflows\.md|projects\.md|relationships\.md|triggers\.md)
---

⚠️ **Direct echo to Elle context file detected!**

You're writing directly to Elle's context memory files.

**Why this matters:**
- Elle context files should be updated thoughtfully, not automatically
- Direct writes bypass the "what changes how I'd respond" principle
- Risk of adding noise instead of signal

**Check before proceeding:**
1. Is this content actually worth persisting between sessions?
2. Does it update understanding of user (identity, preferences, rules)?
3. Should this go through elle-sync or proper context management instead?

**Protected files:**
- `session.md` - Current working session (ephemeral)
- `journal.md` - Append-only notable sessions
- `identity.md` - Who they are
- `preferences.md` - How they work
- `rules.md` - Corrections from past mistakes
- Other core context files in `~/.claude/.context/core/`

**Better approach:**
- Use elle-sync for structured context updates
- Edit files with Read + Edit (allows validation)
- Consider if content belongs in memory at all
