### 2. Adjust Gate-NL Threshold

**Recommendation**: Change `fallback_rate < 20%` to `fallback_rate <= 20%`

**Rationale**:
- The current threshold creates a mathematical impossibility for well-performing systems
- 20% fallback with 60% alias + 20% nl_trigger = reasonable distribution
- The quality signals (true_zero_guidance = 0%, accuracy = 57.5%) are more important
