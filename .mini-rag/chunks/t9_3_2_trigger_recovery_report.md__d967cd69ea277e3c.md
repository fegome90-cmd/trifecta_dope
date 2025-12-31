### Key Improvements

1. **alias_hit_rate reduced by 22.5%**: From 82.5% to 60.0%
   - Tasks now match via L2 direct triggers instead of falling through to L3 alias matching
   - Better separation of canonical phrases from loose term matching

2. **L2 Direct Triggers Working**: 8/40 tasks (20%) match via nl_triggers
   - Examples:
     - "can you show me the token counting logic" → L2 match via "token counting"
     - "where would i find stats about search performance" → L2 match via "search performance"

3. **Accuracy Now Measurable**: plan_accuracy_top1 = 57.5% (23/40)
   - 17 tasks incorrectly predicted (8 fallbacks expected, 9 wrong features)

---
