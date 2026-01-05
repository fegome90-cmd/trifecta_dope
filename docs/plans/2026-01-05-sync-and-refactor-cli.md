# Sync & Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Sync local environment with `origin/main` (to adopt Pyrefly and docs updates) and preserve critical session artifacts. The CLI UX Strategy is TBD (discarded Helpful Failure).

**Architecture:**
- **Step 1 (Safety):** Commit all current work on `fix/mypy-type-errors` to avoid data loss.
- **Step 2 (Sync):** Checkout `main`, pull `origin`, and update dependencies (`uv sync`).
- **Step 3 (Harvest):** Cherry-pick or manually copy the valid artifacts (`braindope.md`, `docs/session_update/*`) from the previous branch.

**Tech Stack:** Python, Typer, Git, Pyrefly (new linter).

---

### Task 1: Secure Current Work

**Files:**
- Modify: `docs/session_update/*` (ensure mostly intact)

**Step 1.1: Verify current status**
Run: `git status`
Expected: Unstaged changes in `braindope.md` and tests.

**Step 1.2: Commit everything**
```bash
git add .
git commit -m "wip: save red team docs and session state"
```

**Step 1.3: Note Commit Hash**
Run: `git rev-parse HEAD`
Expected: A SHA hash to reference later.

---

### Task 2: Sync with Main

**Files:**
- Modify: `pyproject.toml` (will be updated by pull)
- Modify: `uv.lock` (will be updated by pull)

**Step 2.1: Checkout Main**
```bash
git checkout main
```

**Step 2.2: Pull Origin**
```bash
git pull origin main
```

**Step 2.3: Sync Environment**
```bash
uv sync --all-extras
```

**Step 2.4: Verify Pyrefly**
Run: `uv run pyrefly --version` (or help)
Expected: Success.

---

### Task 3: Harvest Artifacts (Cherry-Pick)

**Files:**
- Create: `docs/session_update/*` (restore them)
- Create: `braindope.md` (restore Red Team contract)

**Step 3.1: Restore Braindope & Docs**
```bash
git checkout fix/mypy-type-errors -- braindope.md docs/session_update/
```

**Step 3.2: Verify Preservation**
Run: `ls -l braindope.md docs/session_update/`
Expected: All files present.
