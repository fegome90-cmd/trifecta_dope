### 2. Symmetric Ambiguity Loop

Extended strict 3+1 validation to all context layers:
- **Agents**: Must have exactly one `agent_<segment_id>.md`.
- **Sessions**: Must have **exactly one** `session_<segment_id>.md` (REQUIRED).
   - Missing session: **FAIL** (North Star Compliance).
   - Multiple sessions: **FAIL** (Ambiguity).
- **Contamination**: Presence of `agent_other.md` triggers immediate failure.
