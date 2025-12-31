```
┌──────────────────────────────────────────────────────────────────┐
│ Query → Search → Get Cycle                                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Query 1: "pytest testing validation structure"                 │
│  ├─ Time: 0.5s                                                  │
│  ├─ Results: 0 hits                                             │
│  └─ Reason: Terms not in index                                  │
│                                                                  │
│  Query 2: "validate segment installer test" (refined)           │
│  ├─ Time: 0.8s                                                  │
│  ├─ Results: 5 hits (all scored 0.50)                          │
│  └─ Top Match: agent:39151e4814 [726 tokens]                  │
│                                                                  │
│  Retrieval: ctx get --ids "agent:39151e4814"                   │
│  ├─ Time: 0.3s                                                  │
│  ├─ Tokens Delivered: 726 / 900 budget                          │
│  ├─ Budget Remaining: 174 tokens (19% headroom)                 │
│  └─ Status: WITHIN BUDGET ✅                                    │
│                                                                  │
│  TOTAL SESSION TIME: ~5 seconds
