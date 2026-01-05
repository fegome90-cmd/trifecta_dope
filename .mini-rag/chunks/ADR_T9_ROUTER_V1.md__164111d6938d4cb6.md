## Clamp (Single-Word)
- Applies when trigger word_count == 1 and feature priority >= 4
- Config-driven `support_terms` in `aliases.yaml`
- Allow only if query contains >= 1 support term
- Otherwise block with warning `weak_single_word_trigger`
