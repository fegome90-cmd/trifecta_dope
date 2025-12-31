#### ⚠️ Areas for Improvement

| Issue | Severity | Impact | Recommendation |
|-------|----------|--------|-----------------|
| **Duplicate Chunks** | Medium | +1.7K wasted tokens (12% of pack) | Implement deduplication in v1.1 |
| **Primitive Ranking** | Medium | All results scored 0.50 (no discrimination) | Add TF-IDF or BM25 scoring |
| **Large README** | Medium | 3.054 tokens in 1 chunk (42% of pack) | Fragment by H2 headers (max 4K chars/chunk) |
| **Zero-Hit Queries** | Low | Required 2 attempts to get hits | Add query synonym expansion |
