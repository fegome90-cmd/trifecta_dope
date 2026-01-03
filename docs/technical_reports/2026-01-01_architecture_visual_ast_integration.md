# Architecture Visualization: Trifecta v2 Dual-Engine

This diagram clarifies the relationship between the existing `ctx.search` (Context Engine) and the new AST/LSP logic (Code Engine).

**Key Takeaway**: AST/LSP does **not** replace `ctx.search`. They are parallel tools for different intents.

```mermaid
flowchart TB
    User[Agent / User]

    subgraph DecisionLayer ["Decision Layer (Brain)"]
        Intent{"What do I need?"}
    end

    subgraph EngineA ["Engine A: Context (Concepts)"]
        direction TB
        Search[ctx.search]
        Pack["Context Pack\n(JSON)"]
        Docs["Docs / Prime / Skills"]
    end

    subgraph EngineB ["Engine B: Code (Precision)"]
        direction TB
        Selector["AST/LSP Selector\n(sym://...)"]
        AST[Tree-sitter Parser]
        LSP["LSP Server (Pyright)"]
        LiveCode[Live Source Code]
    end

    subgraph Output ["Output (Context Window)"]
        Result
    end

    User --> Intent

    %% Path A: Conceptual Search
    Intent -- "How does X work?" --> Search
    Search --> Pack
    Pack -.-> Docs
    Search -- "Concept Chunks" --> Result

    %% Path B: Code Navigation
    Intent -- "Show me class X" --> Selector
    Selector --> AST
    Selector --> LSP
    AST -.-> LiveCode
    LSP -.-> LiveCode
    AST -- "Skeleton / Stub" --> Result
    LSP -- "Signature / Diagnostics" --> Result

    %% Interaction
    Result -- "Found Ref: AuthManager" --> Intent

    style Search fill:#e1f5fe,stroke:#01579b
    style Selector fill:#fff3e0,stroke:#e65100
    style Result fill:#f3e5f5,stroke:#4a148c
```

## Workflow Explanation (Progressive Disclosure)

1.  **Phase 1: Discovery (Engine A)**
    *   Agent uses `ctx.search("auth")`.
    *   **Result**: Receives `prime_auth.md` explaining the *concept* of Auth and mentioning `AuthManager` class.

2.  **Phase 2: Navigation (Engine B)**
    *   Agent sees `AuthManager` is relevant.
    *   Instead of `read_file(auth.py)`, Agent uses `ast symbols AuthManager`.
    *   **Result**: Receives **Skeleton** (methods list) of `AuthManager`.

3.  **Phase 3: Inspection (Engine B)**
    *   Agent wants the logic of `login()`.
    *   Agent uses `ast snippet sym://python/AuthManager.login`.
    *   **Result**: Receives only the 10 lines of code for that method.

**Conclusion**: `ctx.search` is the map; AST/LSP is the magnifying glass.
