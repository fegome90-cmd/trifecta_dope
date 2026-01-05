### 4. ❌ "Using mtime for cache invalidation"
**Why bad here:** File regenerated in <1s → mtime == old → stale cache.  
**Lean alternative:** Content SHA-256 for files, structural hash for symbols.
