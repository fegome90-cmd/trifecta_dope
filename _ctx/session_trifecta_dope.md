# session.md - Trifecta Context Runbook

segment: trifecta_dope

## Purpose

This file is a **runbook** for using Trifecta Context tools following the **Agentic Constitution v1.1**.

## Quick Commands (CLI)

### 🛰️ Basic Context (PCC)

```bash
# [Law II] Reading before writing
make sync
make search Q="<topic>"
trifecta ctx get --segment "." --ids "<id>" --mode excerpt
```

### 🧠 Intelligent Discovery (AST & LSP)

```bash
# Discover symbols in Python (Class, Def, Import)
# URI format: sym://python/mod/<path.to.module>
trifecta ast symbols "sym://python/mod/src.infrastructure.cli"

# LSP Hover (Definition + Type info) - Requires Warmup
trifecta ast hover "src/infrastructure/cli.py" --line 1672 --char 5
```

### 🕸️ Relationship Mapping (Graph)

```bash
# Find who calls a specific function
trifecta graph callers --symbol "create"

# Find what functions a specific function calls
trifecta graph callees --symbol "TemplateRenderer.render_skill"
```

### 🩺 System Maintenance

```bash
# [Law V] Verification
trifecta ctx validate --segment "."

# Global Status & Health
make status
make doctor
```

## Rules (must follow)

- Max **1 ctx.search + 1 ctx.get** per user turn.
- Cite evidence using **[chunk_id]** (Law IV & XI).
- **FAIL-CLOSED**: If validate fails, STOP.

## Session Log (append-only)

### Entry Template (Law I & XI)

```md
## YYYY-MM-DD HH:MM - ctx cycle

- Segment: .
- Objective: <Law I: Intencion explicita>
- Plan: ctx sync -> ctx search -> ctx get
- Evidence: <Law IV: Evidencia obligatoria>
- Next: <1 concrete step>
```

### 2026-05-22 06:00-07:00 — SDD fix-collection-errors + Bug Hunt

- Segment: .
- Objective: Fix 3 collection errors blocking test suite; audit CLI with real-world bug hunter
- Plan: SDD (explore→proposal→spec→gate→apply→verify→archive) then bug hunt (ripper+walker+sniper)

**SDD fix-collection-errors** — COMPLETED & ARCHIVED

- Deleted orphan tests: test_sanitizer.py, test_lsp_daemon.py
- Realigned daemon_manager tests (tuple return type, lock path, stale cleanup)
- Fixed restart() return type bug in daemon_manager.py
- Renamed test_daemon_manager.py → test_daemon_manager_unit.py (name collision)
- Committed pending IDF/synthetics test changes
- Result: 2019 collected, 0 errors, 35/35 our tests pass
- Commits: 5cce031c, 6391d651, 01d3736e
- Archive: openspec/changes/archive/2026-05-21-fix-collection-errors/

**Bug Hunt** — 6 findings (2 HIGH, 2 MEDIUM, 2 LOW)

- H1: Daemon starts for arbitrary paths outside ALLOWED_BASES
- H2: Query index crawls .worktrees/ (stale branches indexed)
- M1: ctx reset --force destructive without confirmation
- M2: Graph callers fails on ambiguous symbols with no disambiguation
- Report: docs/reports/bug_hunt_report_2026-05-22.md

**Preexisting issues confirmed**:

- ~79 test failures in validators/strict_validation/t7/acceptance
- test_vague_spanish_query_on_hits_via_expansion broken by d96cee56
- Oracle LSP not wired (fidelity never "full")
- Graph stale >7 days

- Evidence: 2019 collected 0 errors; 20/20 daemon tests pass; bug hunt report with reproduction steps
- Next: Create SDD change for H1 (daemon path validation) and H2 (worktree exclusion) if desired

### 2026-05-22 07:48 -04 — Review of SDD git-hygiene-audit

- Segment: .
- Objective: Verify whether `openspec/changes/git-hygiene-audit` is well elaborated before execution.
- Plan: read proposal/spec -> compare against current git state -> report gaps and risks.
- Evidence: `git status --short --branch` shows `main...origin/main [ahead 12]`; `git branch -r --no-merged main` shows 7 remote branches; `git count-objects -vH` reports 2 garbage objects / 13.71 MiB; `git diff --stat` shows REQ-09 scope is much larger than "formatting + metadata only" because `reconcile.patch` dominates the diff.
- Next: If requested, convert the review into concrete corrections for `DESIGN.md` + `TASKS.md` and tighten REQ-09 acceptance criteria.

### 2026-05-22 07:51 -04 — Root causes captured for weak git-hygiene-audit SDD

- Segment: .
- Objective: Preserve why the agent generated a weak SDD so the mistake pattern is reusable.
- Plan: distill root causes from proposal/spec vs live repo evidence -> save to memory -> log here.
- Evidence: proposal mixes hygiene with publish/push work; proposal count says 5 stale branches while listing 6; proposal names `stash-preserve-codex-fallback-v1` while repo/spec use `stash-preserve-codex-freeze-v1`; spec stops at proposal+spec with no design/tasks; dirty diff is huge, so REQ-09 risk classification is wrong.
- Next: If requested, I can turn these causes into a prevention checklist for future SDD generation.

### 2026-05-22 08:13 -04 — Apply gate decision for publish-main-backlog

- Segment: .
- Objective: Decide whether `publish-main-backlog` is ready for apply after the new gate output.
- Plan: verify gate claims against `SPEC.md`/`TASKS.md` -> decide if apply can proceed safely.
- Evidence: `publish-main-backlog/TASKS.md` T2.3 still uses blanket `git add _ctx/ my_project/_ctx/`; `git-hygiene-cleanup/TASKS.md` T2.3 still batches remote deletes; both match the reported medium findings.
- Next: Recommend proceeding with `publish-main-backlog` only after hardening T2.3 so apply does not stage whole directories blindly.

### 2026-05-22 08:20 -04 — Skill-hub impact verification for pending git changes

- Segment: .
- Objective: Verify whether `publish-main-backlog` / `git-hygiene-cleanup` would damage `skill-hub`.
- Plan: compare touched files vs skill-hub implementation surface, then run targeted skill-hub tests.
- Evidence: `git diff --name-only` shows no `skill_hub*` implementation files are touched; `src/application/skill_hub_indexing_strategy.py` explicitly says segment metadata files like `skill.md` are excluded from skill indexing; targeted skill-hub tests show many preexisting failures plus two integration failures caused by AGENTS.md constitution expectations in temp fixtures, not by the pending git hygiene changes.
- Next: Safe to say there is no direct new damage path to skill-hub from these changes, but not safe to claim skill-hub is fully healthy on this branch.
