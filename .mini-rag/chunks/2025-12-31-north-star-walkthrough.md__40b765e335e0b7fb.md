### 1. Fail-Closed Legacy Enforcement

The system now treats legacy files (`agent.md` without suffix) as a **Critical Error**.
- **Old Behavior**: Warning (yellow).
- **New Behavior**: Exit Code 1 (Fail-Closed).
