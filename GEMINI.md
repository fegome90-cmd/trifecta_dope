# Gemini Agent Memory (Local Project Mirror)

## 🛑 MANDATORY: Session Logging & Persistence

**Rule 1: Use the CLI**  
You must use the `trifecta` CLI for all agentic workflows. Do not run loose scripts unless constructing a specific harness.

**Rule 2: Audit-Grade Logging**  
Upon completing a task, you MUST append a session summary to the `_ctx/session_trifecta_dope.md` file (Project-local).
Also append audit-grade summary to `HISTORY.md` in global logic when appropriate.

**Rule 3: Superpowers**  
Check `skill.md` or global superpowers.

---

## 🧠 Project Context / Memories (Trifecta)

### Learned Patterns (Sprint Lessons)
- **Feature Flag Scope**: `pytest-env` (tests) != `.envrc` (Dev CLI).
- **Backlog Governance**: Single source of truth. Use `git mv`, never copy.
- **Audit-Grade Gates**: Verify internal state (telemetry, DB files), not just exit code.

### Architecture & Style
- **Architecture**: Domain (Pure) → Application → Infrastructure.
- **Evidence**: Fail-closed. Raw logs required before "Done".

---

## 📜 History (Project Specific)
See `_ctx/session_trifecta_dope.md` for full detailed runbook.
See `_ctx/telemetry/events.jsonl` for raw events.
