### Expected Warnings

| Warning Type | Expected Count | Actual Count | Notes |
|-------------|----------------|--------------|-------|
| ambiguous_single_word_triggers | 1 | 0 | "telemetry architecture overview" - correctly falls back |
| match_tie_fallback | 0 | 0 | No ties detected |

**Note**: "architecture" (task #27) correctly falls back because arch_overview.priority=2 < 4 (guardrail working).

---
