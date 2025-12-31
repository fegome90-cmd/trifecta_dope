```
┌─────────────────────────────────────────────────────────────────────────┐
│ DESIRED STRUCTURE (Clean Architecture Compliant)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  scripts/                                                                │
│  ├─ install_trifecta_context.py  [REFACTORED]                           │
│  │  └─ from src.infrastructure.validators import validate_segment      │
│  │                                                                       │
│  tests/                                                                  │
│  ├─ installer_test.py  [CLEAN]                                          │
│  │  └─ from src.infrastructure.validators import validate_segment_structure
│  │  └─ No sys.path hacks                                               │
│  │                                                                       │
│  src/                                                                    │
│  ├─ domain/          (pure logic)                                        │
│  ├─ application/     (use cases)                                         │
│  ├─ infrastructure/                                                      │
│  │  ├─ validators.py  [NEW] ✨                                          │
│  │  │  └─ validat
