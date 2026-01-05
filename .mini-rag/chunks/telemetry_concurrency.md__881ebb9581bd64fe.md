### 2. In-Memory Queue + Background Writer

**Pros:** No blocking, high throughput  
**Cons:** Complex (requires thread/process management), queue size limits, memory pressure, events lost on crash  
**Verdict:** Over-engineered for simple JSONL logging
