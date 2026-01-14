---
name: warn-execution-intent
enabled: true
event: stop
action: warn
pattern: .*
---

⚠️ **Verify Execution Intent Before Proceeding**

Before executing or stopping, confirm the user's intent:

**Key questions to ask yourself:**

1. **Did the user say "prepare" or "get ready"?**
   - If yes → They want setup/planning, NOT execution yet
   - Create plan, document, but DON'T start implementing

2. **Did the user say "in another session" or "separate session"?**
   - If yes → Prepare for FUTURE execution, NOT now
   - Create plan file, provide instructions for next session

3. **Did the user explicitly say "execute now" or "do it"?**
   - Only proceed with implementation if EXPLICITLY confirmed

**Common confusion patterns:**
- "planificar" (plan) → Create plan, don't execute
- "preparar" (prepare) → Get ready, don't start
- "otra sesión" (another session) → Different session, not this one

**If unsure, ASK:**
- "Do you want me to execute this now, or prepare for another session?"
- "Should I implement this, or just create the plan?"

**Context from conversation:** User corrected me when I started executing code changes when they wanted preparation for a separate multi-agent session.
