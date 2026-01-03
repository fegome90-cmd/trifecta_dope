---
name: debug-code-left-in
enabled: true
event: file
pattern: (console\.log\(|pp\s+|pdb\.set_trace\(|breakpoint\(\)|TODO.*fix|FIXME|print\(|\.debug\(|logger\.debug)
action: warn
---

⚠️ **DEBUG CODE DETECTED**

Debug code or markers left in production files.

**Before committing:**
- Remove console.log/print/pp
- Remove breakpoints
- Address or move TODO/FIXME to tracking system

**This violation will be logged to Obsidian on next sync.**
