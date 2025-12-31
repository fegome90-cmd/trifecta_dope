### 1. Fix Unigram Matching for NL Triggers

**Problem**: Single-word nl_triggers like "telemetry" and "architecture" aren't matching.

**Solution**: Update `_normalize_nl()` to always include unigrams, not just when there are 2+ tokens.

```python
# Current: only generates bigrams when len(tokens) >= 2
tokens = normalized.split()
unigrams = tokens
bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
return unigrams + bigrams

# This should already work, but need to verify single-word triggers are in nl_triggers[]
```
