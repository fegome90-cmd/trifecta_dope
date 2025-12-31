[NEW] ✨                                          │
│  │  │  └─ validate_segment_structure() ◄─── MOVED HERE (proper location)
│  │  │  └─ ValidationResult (dataclass)                                  │
│  │  │                                                                    │
│  │  └─ file_system.py  [FIXED]                                          │
│  │     ├─ REFERENCE_EXCLUSION = {"skill.md"}                            │
│  │     └─ Skip ref-indexing for excluded files ◄─── DEDUPLICATION FIX   │
│  │                                                                       │
│  _ctx/context_pack.json  [OPTIMIZED]                                    │
│  ├─ 6 chunks total (was 7)                                              │
│  ├─ skill.md appears 1x only                                            │
│  └─ -1.7K tokens, cleaner index                                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

BENEFITS:
  ✅ Clean Architecture compliant
  ✅ Domain logic in proper layer
  ✅ Standard Python imports
  ✅ No test hacks
  ✅ Deduplication (-12% pack size)
```
