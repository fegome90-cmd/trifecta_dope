```
┌─────────────────────────────────────────────────────────────────────────┐
│ CURRENT STRUCTURE (Clean Architecture Violation)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  scripts/                                                                │
│  ├─ install_FP.py                                                       │
│  │  └─ validate_segment_structure() ◄─── DOMAIN LOGIC IN SCRIPTS        │
│  │                                                                       │
│  └─ install_trifecta_context.py                                         │
│     └─ Uses: validate_segment()                                         │
│                                                                          │
│  tests/                                                                  │
│  ├─ installer_test.py                                                   │
│  │  └─ sys.path.insert() workaround ◄─── HACK: Add scripts/ to path     │
│  │  └─ from install_FP import validate_segment_structure                │
│  │                                                                       │
│  src/                                                                    │
│  ├─ domain/          (pure logic, no dependencies)                       │
│  ├─ application/
