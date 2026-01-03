---
name: metodo-p2-non-deterministic
enabled: true
event: all
pattern: (sleep\(|time\.sleep|pytest\.mark\.skip|@pytest\.fixture.*autouse|flaky|xfail)
action: warn
---

🟡 **P2 VIOLATION DETECTED: Non-Deterministic Test**

Test contains timing dependencies or skip markers that can cause flakes.

**Why this is risky:**
- CI failures unrelated to code changes
- False positives/negatives
- Unreliable test suite

**Fix pattern:**
- Replace sleep with proper async/await
- Use contract-based outputs instead of skipping
- Make tests deterministic and fast

**This violation will be logged to Obsidian on next sync.**
