# Gemini Agent Memory

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

**Rule 5: Superpowers**  
If `superpowers` are mentioned, check `skill.md` or global superpowers, specifically `~/.claude/skills/superpowers`.

---

## ⚡️ Trifecta CLI Protocol (See [skill.md](file:///Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/skill.md))

**Core Environment**: `uv` package manager + `fish` terminal.

### 1. Basic Workflow
```bash
make install              # Sync dependencies
uv run trifecta --help    # View CLI capabilities
uv run pytest             # Run all tests
make gate-all             # Run full verification (Unit+Int+Acceptance)
```

### 2. Context Cycle (Search → Get)
Do not guess files. Use the context engine:
```bash
# A. Search (Instruction-based, NOT keywords)
uv run trifecta ctx search --segment . --query "How to implement file locking in sqlite cache" --limit 5

# B. Get (Chunk-based)
uv run trifecta ctx get --segment . --ids "infra:cache_v1,doc:design_p2" --mode excerpt
```

### 3. Backlog Governance
- **Registry**: `_ctx/backlog/backlog.yaml` (Epic Source of Truth)
- **Work Orders**: `_ctx/jobs/{pending,running,done}/*.yaml`
- **Validation**: `python scripts/ctx_backlog_validate.py --strict`
- **Rule**: `verified_at_sha` MUST be an explicit SHA, never "HEAD".

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

## 📜 History

> **Moved to separate file:** `HISTORY.md`
> Valid session summaries should be appended to `/Users/felipe_gonzalez/.gemini/HISTORY.md`.
