## 2. Adjusted Stability Metrics (Corrected)

Filtering out false positives (LSP lifecycle, Stub regen):

| Subsystem | Adjusted Success Rate | Real Error Types |
|---|---|---|
| **PCC (Search/Get)** | **99.3%** | Very stable. Rare generic faults. |
| **Core (Sync)** | **90%** (est) | Primary error: `SEGMENT_NOT_INITIALIZED` (Feature, not bug). |
| **AST / M1** | **100%** | `n=35`. Zero failures recorded. |

---
