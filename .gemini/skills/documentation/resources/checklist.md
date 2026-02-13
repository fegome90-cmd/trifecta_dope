# Implementation Checklist

Use this checklist before committing any onboarding documentation updates.

## Layer 1: CRITICAL Section

- [ ] CRITICAL section exists at the top (before Quick Start, Architecture, etc.)
- [ ] Starts with `## ⚠️ CRITICAL: READ THIS FIRST BEFORE ANY TASK`
- [ ] Contains `**DO NOT PROCEED WITH ANY TASK WITHOUT READING THESE CONTEXT FILES.**`
- [ ] Specifies mandatory files to read with numbered list (0, 1, 2, 3)
- [ ] Each file has time estimate: `← START HERE (3 min)`, `← THEN READ (5 min)`, etc.
- [ ] Each file entry has explicit consequence: "Skip this → you'll [negative outcome]"
- [ ] Includes "**If You Skip These Files**" section
- [ ] "If You Skip" section has ⛔ column (what will go wrong)
- [ ] "If You Skip" section has ✅ column (correct approach)
- [ ] Total mandatory files ≤ 5 (ideally 3-4)
- [ ] Total read time ≤ 15 minutes

## Symbols & Typography

- [ ] ⚠️ used only for CRITICAL layer (not overused)
- [ ] ⛔ used in negative consequences sections
- [ ] ✅ used in positive/correct approach sections
- [ ] ← arrows used to guide eye to file names
- [ ] All file references are **bold or markdown links**
- [ ] Capitalized phrases: "**DO NOT PROCEED**", "**MANDATORY**", "**CRITICAL**"
- [ ] No ALL CAPS except in headings (hard to read)

## File References

- [ ] All file paths are markdown links: `[skill.md](skill.md)` (not plain text)
- [ ] No absolute paths (e.g., `/Users/username/...` or `C:\Users\...`)
- [ ] No stale paths (e.g., old repo references)
- [ ] Relative paths use `./` for current dir or `_ctx/filename` for context files
- [ ] Links are valid and would work if clicked

## Consistency Across Files

- [ ] CLAUDE.md and agents.md have identical CRITICAL sections (or clearly noted differences)
- [ ] Same mandatory files listed in both
- [ ] Same time estimates in both
- [ ] Same consequences listed in both
- [ ] File references and paths match exactly between files
- [ ] No conflicting instructions between files

## Language & Tone

- [ ] Uses imperatives: "Read X", "Start here", (not "You should read")
- [ ] Uses explicit negation: "DO NOT PROCEED" (not "Be sure to read")
- [ ] Uses contract language: "breach of the work contract" where appropriate
- [ ] Consequences are specific: "Skip → you'll duplicate work" (not "Skip → you'll have problems")
- [ ] Time estimates are reasonable (can agent really read in 3 min?)
- [ ] Consequences are credible (would agent actually hit these problems?)

## Structure & Organization

- [ ] Quick Start section comes AFTER CRITICAL section
- [ ] Architecture/Pattern sections come after Quick Start
- [ ] Reference/lookup content comes last
- [ ] Heading hierarchy makes sense (# → ## → ###)
- [ ] No critical info buried at bottom of file
- [ ] Section flow matches "4 layers of documentation" pattern

## Quality Gates

- [ ] Spell-checked and grammar-correct
- [ ] Links tested (not broken)
- [ ] Code examples (if any) are valid
- [ ] No excess whitespace or formatting errors
- [ ] Markdown renders correctly (check in preview)
- [ ] Line length reasonable (not >120 chars per line)

## Final Verification

- [ ] Read entire file as new user - does it work?
- [ ] Count how many times agent would be interrupted with critical info (target: immediately)
- [ ] Test: would an agent skip the CRITICAL section? If yes, make it more distinctive
- [ ] Compare with `examples/CLAUDE_md_good_vs_bad.md` - does yours follow the pattern?
- [ ] Run `verify_documentation.sh` - no errors?

---

**Ready to commit?** If all boxes checked, documentation is audit-ready.
