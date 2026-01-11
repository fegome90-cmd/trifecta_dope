## 🚀 What's Included
1.  **Plan A (Programmatic Context Calling)**:
    - `ctx search`: Lexical search with top-k limits.
    - `ctx get`: ID-based retrieval with budget awareness (value-per-token sorting).
2.  **Plan B (Fallback Strategy)**:
    - `load --mode fullfiles`: Resilient loading when packs are missing or access is critical.
3.  **Strict Validation Gates**:
    - Atomic writes (`_ctx/.autopilot.lock`).
    - Fail-closed validation (SHA-256 deep checks).
4.  **Dumb Macro Sync**:
    - `ctx sync`: Fixed macro (`build` + `validate`) for deterministic state.
