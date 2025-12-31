### CLI Report

```
$ trifecta telemetry report --last 7d

╭─────────────────────────────────────────────────╮
│         Trifecta Telemetry Report                │
│              Last 7 days                         │
╰─────────────────────────────────────────────────╯

Summary
───────────────────────────────────────────────────
  Total commands:      49
  Unique sessions:     3
  Avg latency:         1.2ms

Top Commands
───────────────────────────────────────────────────
  ctx.search           19  (38.8%)
  ctx.sync             18  (36.7%)
  ctx.get               6  (12.2%)
  load                  4  ( 8.2%)
  ctx.build             2  ( 4.1%)

Search Effectiveness
───────────────────────────────────────────────────
  Total searches:      19
  With hits:            6  (31.6%)
  Zero hits:           13  (68.4%)  ⚠️

Recent Queries (Failed)
───────────────────────────────────────────────────
  "telemetry class"            → 0 hits
  "validators deduplication"    → 0 hits
  "sequential thinking"         → 0 hits
```
