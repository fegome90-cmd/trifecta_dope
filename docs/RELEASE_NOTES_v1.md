# Trifecta Context Loading v1 — Release Notes

**Status**: Verified & Ready for Integration
**Date**: 2025-12-29

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

## ⚠️ Known Limitations (v1)
- **No Embeddings**: Search is purely lexical (grep-like heuristics).
- **Documentation Only Contracts**: `session.md` YAML is for reference; not executed by the system.
- **Segment-Local Only**: No global index; operations are scoped to the current segment.

## 🛠️ Usage Guide (Top 5 Commands)

### 1. Build & Sync (Routine Maintenance)
```bash
trifecta ctx sync --segment .
```

### 2. Search (Discovery)
```bash
trifecta ctx search --segment . --query "authentication" --limit 5
```

### 3. Get Context (retrieval)
```bash
trifecta ctx get --segment . --ids "skill:1,agent:3" --budget-token-est 1000
```

### 4. Create New Pack (Setup)
```bash
make trifecta-create SEGMENT=my-feature PATH=.
```

### 5. Fallback Load (Emergency)
```bash
trifecta load --segment . --task "rescue mission" --mode fullfiles
```

## 🐛 Bug Reporting
Attach the following files:
- `_ctx/autopilot.log` (if available)
- `_ctx/context_pack.json`
- `_ctx/validation_report.json` (if verification fails)
