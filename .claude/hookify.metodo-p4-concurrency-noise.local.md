---
name: metodo-p4-concurrency-noise
enabled: true
event: all
pattern: (stderr.*Daemon|ThreadPool.*shutdown|RuntimeError.*loop|stderr.*poll|RaceCondition|deadlock)
action: warn
---

🟠 **P4 VIOLATION DETECTED: Concurrency/Shutdown Issue**

Race condition or lifecycle management problem detected.

**Why this is risky:**
- Intermittent test failures
- stderr pollution
- Unpredictable behavior

**Fix pattern:**
- Add proper lifecycle hardening
- Use tripwire tests for shutdown
- Clean daemon shutdown protocols

**This violation will be logged to Obsidian on next sync.**
