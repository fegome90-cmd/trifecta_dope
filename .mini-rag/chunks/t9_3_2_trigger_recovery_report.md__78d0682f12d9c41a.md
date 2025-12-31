### Root Cause Analysis

The NL trigger matching isn't catching all expected matches:

| Task | Expected NL Trigger | Why It Should Match | Actual Outcome |
|------|---------------------|---------------------|----------------|
| "list all typer commands available" | "list commands" | "list" + "commands" bigram | Fallback |
| "telemetry" | "telemetry statistics" | "telemetry" unigram | Fallback |
| "architecture" | "repo architecture" | "architecture" unigram | Fallback |

**Issue**: The current implementation only matches if the exact trigger phrase appears in the normalized ngrams. For single-word triggers like "telemetry", we need to ensure unigram matching works.

**Fix**: Add unigram support to nl_trigger matching (currently only bigrams are generated for multi-word phrases).

---
