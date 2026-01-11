### 3. Separate Telemetry Process

**Pros:** Complete isolation, no contention  
**Cons:** IPC overhead (sockets/pipes), process management complexity, events lost if process crashes  
**Verdict:** Too complex for current scale
