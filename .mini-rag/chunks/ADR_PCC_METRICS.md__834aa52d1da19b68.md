### 1. Tie-Breaking Rule: Tie → Fallback

**Rule:** When multiple features have equal scores, prefer fallback to avoid arbitrary selection.

**Implementation:** Ties are resolved by selecting "fallback" as `selected_by`.

**Rationale:** Deterministic behavior is preferable to random selection. Fallback provides a safe default when confidence is equal.
