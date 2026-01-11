### 1. ❌ "Indexing everything in memory"
**Why bad here:** 5k files × 100KB skeleton = 500MB RAM upfront.  
**Lean alternative:** Lazy-load skeletons, LRU cache (100-file limit), persistent index.
