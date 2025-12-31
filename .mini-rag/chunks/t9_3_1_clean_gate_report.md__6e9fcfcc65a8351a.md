### Recommendation

Consider adjusting the Gate-NL alias_hit_rate threshold from **<= 70%** to **<= 85%** to account for:
1. NL-only datasets naturally have higher alias rates (no L1 explicit features)
2. Well-performing systems with good trigger coverage will exceed 70%
3. The fallback_rate (< 20%) and true_zero_guidance (= 0%) are the more important quality signals

---
