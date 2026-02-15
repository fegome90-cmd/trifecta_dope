# Gemini Agent Memory & Operational Manual

## 🛑 MANDATORY: Session Logging & Persistence

**Rule 1: Use the CLI**
You must use the `trifecta` CLI for all agentic workflows. Do not run loose scripts unless constructing a specific harness.

**Rule 2: Audit-Grade Logging**
Upon completing a task, you MUST append a session summary to the `_ctx/session_trifecta_dope.md` file (Project-local).
Also append audit-grade summary to `HISTORY.md` in global logic when appropriate.

**Rule 3: Work Order Governance**
Update the relevant WO YAML (`_ctx/jobs/...`) and `_ctx/backlog/backlog.yaml` immediately upon task completion.
- Status: `pending` -> `running` -> `done`
- SHA: `verified_at_sha` (explicit commit)

**Rule 4: Commit Discipline**
Commits MUST run pre-commit hooks. Do NOT use `--no-verify` unless managing a WIP or emergency hotfix.

**Rule 5: Skill Discovery & Superpowers**
Las skills del repositorio están disponibles nativamente en `.gemini/skills/`. Actívalas con `activate_skill(name="...")`.
- **Repo Skills**: `wo-workflow`, `wo-lint-formatter`, `documentation`, `trifecta_dope`.
- **Superpowers**: `writing-plans`, `executing-plans`, `systematic-debugging`, `test-driven-development`, `using-git-worktrees`, etc.

**Rule 6: Delivery Dynamics (Superpower Chain)**
All work must follow this strict sequence of Superpower invocation:
1. `writing-plans` (Design)
2. `test-driven-development` (Implementation)
3. `verification-before-completion` (Self-Audit)
4. `requesting-code-review` (Final Approval)
5. `systematic-debugging` (If issues arise)

---

## ⚡️ Trifecta CLI Protocol

**Core Environment**: `uv` package manager + `fish` terminal.

### 1. Basic Workflow
```bash
make install              # Sync dependencies
uv run trifecta --help    # View CLI capabilities
uv run pytest             # Run all tests
make gate-all             # Run full verification (Unit+Int+Acceptance)
```

### 2. Context Cycle (Search → Get)
Do not guess files. Use the context engine with **instructions**, not keywords.

**A. Search (Instruction-based)**
```bash
uv run trifecta ctx search --segment . \
  --query "Find documentation about how to implement file locking in sqlite cache" \
  --limit 5
```

**B. Get (Chunk-based)**
```bash
# Use excerpt first to confirm relevance, then full if needed
uv run trifecta ctx get --segment . --ids "infra:cache_v1,doc:design_p2" --mode excerpt --budget-token-est 900
```

### 3. Session Evidence Protocol (The 4-Step Cycle)
1. **PERSIST intent**: `trifecta session append --segment . --summary "..."`
2. **SEARCH**: Find relevant context via `trifecta ctx search`.
3. **GET**: Confirm via `trifecta ctx get`.
4. **RECORD result**: `trifecta session append --segment . --summary "Completed: ..."`

### 4. Backlog Governance
- **Registry**: `_ctx/backlog/backlog.yaml` (Epic Source of Truth)
- **Work Orders**: `_ctx/jobs/{pending,running,done}/*.yaml`
- **Validation**: `python scripts/ctx_backlog_validate.py --strict`
- **Rule**: `verified_at_sha` MUST be an explicit SHA, never "HEAD".

---

## 🧠 Skills & Superpowers

Para evitar latencia y saturación de contexto, el agente debe activar skills específicas en lugar de leer archivos de documentación extensos.

### 🛠️ Core Skills
*   **`trifecta_dope`**: Reglas de búsqueda, persistencia de sesión y protocolos del segmento.
*   **`wo-workflow`**: Guía paso a paso para el ciclo de vida de Work Orders.
*   **`wo-lint-formatter`**: Validación de contratos YAML y formato de WOs.
*   **`documentation`**: Estándares para reportes y manuales técnicos.

### ⚡ Superpowers (Metodología Expert)
Usa los "Superpowers" para asegurar una ejecución de grado auditoría:
- `writing-plans`: Antes de cualquier cambio complejo.
- `using-git-worktrees`: Para aislamiento total en WOs.
- `test-driven-development`: Para asegurar cobertura desde el inicio.
- `systematic-debugging`: Para fallos inesperados.

> **Comando**: `activate_skill(name="executing-plans")`

---

## 🧠 Persistent Context / Memories

### User Preferences
- **IDE**: Antigravity (Google-internal).
- **Project**: `agente_de_codigo` / `trifecta_dope`.
- **Terminal**: `fish`.
- **Style**: Fail-closed, audit-grade evidence, no "humo" (smoke/fluff).
- **Architecture**: Domain (Pure) → Application → Infrastructure. Reference `CLAUDE.md` for architectural red flags.

### Learned Patterns (Optimization)
- **Gates**: User prefers *deterministic* gates (boolean) over flaky performance metrics (p95).
- **Soak Testing**: Should be done via dedicated harnesses (scripts), not intertwined with `pytest`.
- **Evidence**: Always provide raw logs/evidence before claiming "Done".

#### Sprint Lessons: Feature Flags & Governance
- **Scope Separation**: `pytest-env` (Tests) != `.envrc`/direnv (Dev CLI). Test config does not verify Dev behavior.
- **Rollback**: "Default ON" claim must be backed by verifying "Override OFF" via env var.
- **Backlog**: WOs are atomic state files. Use `git mv` only. Duplicate files break toolchains.
- **Verification**: `exit 0` is weak. Strong gates assert internal state (e.g. `backend == FileLocked`, `.db` file exists).

---

## 🚫 Anti-Patterns & Violations (Hookify Rules)

| Violation | Code | Description | Fix |
|-----------|------|-------------|-----|
| **Stringly-Typed** | P1 | Using string matching for error/type checks. | Use `isinstance(e, ErrorType)` or match/case. |
| **Non-Deterministic** | P2 | `sleep`, `flaky`, `xfail`, or timing deps. | Use async/await, contract-based outputs. |
| **CWD Coupling** | P3 | Relative paths (`..`), `os.getcwd()`. | Use `segment_root / "file"`, absolute paths. |
| **Concurrency Noise** | P4 | Race conditions, stderr pollution, bad shutdown. | Harden lifecycle, tripwire tests, clean threads. |
| **Env Precedence** | P5 | Unclear env vs flag precedence. | Explicit precedence table, single source of truth. |
| **Secrets/Debug** | - | Hardcoded secrets, `console.log`, `pdb`. | Use env vars, remove debug code. |

### 🚨 Protocol Violations Log (Process Errors)

| Date | Protocol | Violation | Correction |
|:-----|:---------|:----------|:-----------|
| 2026-01-11 | Worktree Isolation | Executed WO fix in `main` worktree instead of isolated one. | Always run `using-git-worktrees` before starting WO tasks. |

---

## 📜 History

> **Moved to separate file:** `HISTORY.md`
> Valid session summaries should be appended to `/Users/felipe_gonzalez/.gemini/HISTORY.md`.