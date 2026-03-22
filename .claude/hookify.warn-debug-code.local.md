---
name: warn-debug-code
enabled: true
event: file
pattern: (console\.log\(|print\(|debugger|breakpoint\(|pprint\.pp\(|logging\.debug\()
---

⚠️ **DEBUG CODE DETECTED**

Debug code or markers detected in production files.

**Before committing:**
- Remove console.log/print/pprint
- Remove breakpoints
- Address or move TODO/FIXME to tracking system

**This violation will be logged to Obsidian on next sync.**
