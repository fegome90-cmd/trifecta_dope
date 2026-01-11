## 4. Stability Assessment

| Subsystem | Stability | Note |
|---|---|---|
| **PCC (Search/Get)** | 🟢 **High** (99%+) | Proven stable. 400+ executions with minimal faults. |
| **Core** | 🟡 **Medium** (75%) | Heavily stressed by negative testing (Error Cards). Real failure rate is lower. |
| **LSP Infra** | 🟡 **Volatile** | Expected volatility due to chaos/resilience testing (`lsp.fallback`). |
| **AST / M1** | ⚪ **Insufficient Data** | 100% Success (`n=35`), but volume (1.6%) is too low to statistically prove stability. |

---
