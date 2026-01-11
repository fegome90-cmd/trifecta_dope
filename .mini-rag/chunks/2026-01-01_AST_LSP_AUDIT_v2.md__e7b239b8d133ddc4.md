### 5. ❌ "Protecting everything with locks"
**Why bad here:** Deadlock risk, contention, complexity.  
**Lean alternative:** Minimal locks (context_pack.json write, session append), append-only logs.
