re logic, no dependencies)                       │
│  ├─ application/     (use cases)                                         │
│  ├─ infrastructure/  (CLI, I/O, templates)                              │
│  │  └─ file_system.py                                                   │
│  │     └─ Indexing: ALL .md files captured 2x ◄─── DUPLICATION BUG      │
│  │                                                                       │
│  _ctx/context_pack.json                                                 │
│  ├─ 7 chunks total                                                      │
│  ├─ skill.md appears 2x: skill + ref:skill.md                           │
│  └─ +1.7K wasted tokens (12% of pack)                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

PROBLEMS:
  ❌ validate_segment_structure() in scripts/ (should be in src/)
  ❌ Tests importing from scripts/ (non-standard Python)
  ❌ sys.path hack in test file
  ❌ Duplicate skill.md chunks in index
```
