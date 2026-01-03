---
name: metodo-p5-env-precedence
enabled: true
event: all
pattern: (os\.environ\.get.*os\.environ|getenv.*default.*getenv|flag.*env.*flag|config.*env.*config)
action: warn
---

🟠 **P5 VIOLATION DETECTED: Env/Flag Precedence Issue**

Unclear precedence between environment variables and flags.

**Why this is risky:**
- Unpredictable behavior
- Configuration conflicts
- Hard to debug

**Fix pattern:**
- Document precedence table explicitly
- Use single source of truth
- Test precedence order

**This violation will be logged to Obsidian on next sync.**
