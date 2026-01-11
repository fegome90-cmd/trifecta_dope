### 2.2 Integration Wiring (Critical)
*   **Plan (T7)**: Progressive Disclosure (Map -> Snippet -> File).
*   **Actual**: `src/application/use_cases.py` and `search_get_usecases.py` are purely legacy logic. `ContextService` does not know about AST skeletons.
*   **Impact**: The "Progressive Disclosure" feature is non-existent.
