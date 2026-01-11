### 1. Blocking Locks (`fcntl.LOCK_EX` without `LOCK_NB`)

**Pros:** 100% event retention, no drops  
**Cons:** Adds latency to every telemetry call, can block agent code, deadlock risk if lock held during agent crash  
**Verdict:** Rejected - telemetry MUST NOT slow down agent
