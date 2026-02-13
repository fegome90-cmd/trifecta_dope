# Codex Learning + Evolve Replication Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replicar en Codex el sistema de learning/evolve de Everything Claude Code con un núcleo funcional (captura, almacenamiento, status, import/export, evolve) y separando lo ya implementable de lo opcional.

**Architecture:** Sistema local con eventos observados + unidad atómica `instinct` + evolución por clustering. Se implementa primero un MVP deterministico en scripts CLI, luego integración opcional con hooks/automations.

**Tech Stack:** Markdown skills, Python CLI local, JSONL para observaciones, directorios en `~/.codex/homunculus/`.

## Scope Findings (Second Pass)

- v1 (`continuous-learning`) es ligero: hook `Stop` + script que solo valida sesión y emite señal de evaluación; no hace extracción real automática en ese script.
- v2 (`continuous-learning-v2`) sí tiene piezas ejecutables reales:
  - `hooks/observe.sh`: captura eventos de hook y persiste `observations.jsonl`.
  - `scripts/instinct-cli.py`: `status`, `import`, `export`, `evolve --generate`.
  - `agents/start-observer.sh`: loop background que invoca `claude --model haiku` para análisis y creación de instincts.
- `/plan` en ECC fuerza confirmación antes de tocar código; esta regla debe quedar explícita en el sistema Codex.
- Parte de la doc es aspiracional (por ejemplo observer “ideal” en markdown) y parte es implementación concreta (scripts shell/python).

## Phase 0: Contract First (No behavior changes)

### Task 1: Freeze product contract

**Files:**
- Create: `docs/plans/2026-02-13-codex-learning-evolve-contract.md`

**Step 1: Write contract doc skeleton**
Include: goals, non-goals, storage paths, command surface, privacy constraints.

**Step 2: Encode v1/v2 parity map**
Document what will be parity-now vs parity-later.

**Step 3: Add acceptance criteria**
Define pass/fail for capture, instinct lifecycle, evolve output.

**Step 4: Commit**
`git commit -m "docs: define codex learning/evolve contract"`

## Phase 1: Filesystem and Data Model

### Task 2: Create codex homunculus layout spec

**Files:**
- Modify: `/Users/felipe_gonzalez/.codex/skills/codex-learning-system/resources/01-system-analysis.md`
- Create: `/Users/felipe_gonzalez/.codex/skills/codex-learning-system/resources/05-data-model.md`

**Step 1: Define root paths**
`~/.codex/homunculus/{observations.jsonl,instincts/{personal,inherited},evolved/{skills,commands,agents}}`

**Step 2: Define instinct schema**
YAML frontmatter required fields: `id, trigger, confidence, domain, source`.

**Step 3: Define observation schema**
JSONL event contract with timestamp/event/tool/session/input/output (truncated).

**Step 4: Commit**
`git commit -m "docs: add codex learning data model and storage spec"`

## Phase 2: CLI Core (Deterministic MVP)

### Task 3: Build codex instinct CLI

**Files:**
- Create: `/Users/felipe_gonzalez/.codex/skills/codex-learning-system/resources/scripts/instinct_cli.py`
- Create: `/Users/felipe_gonzalez/.codex/skills/codex-learning-system/resources/06-cli-usage.md`
- Create: `tests (if this repo will host scripts): tests/unit/test_instinct_cli.py`

**Step 1: Write failing tests for parser and load logic**
Cases: md/yaml parsing, malformed frontmatter handling.

**Step 2: Implement `status`**
Group by domain, confidence sorting.

**Step 3: Implement `import`**
Local path + URL support, duplicate/update policy.

**Step 4: Implement `export`**
Filter by domain/confidence.

**Step 5: Implement `evolve` + optional generate**
Cluster by trigger similarity, emit evolved artifacts.

**Step 6: Verify with tests**
Run targeted unit tests and sample CLI runs.

**Step 7: Commit**
`git commit -m "feat: add codex instinct cli with status/import/export/evolve"`

## Phase 3: Observation Capture

### Task 4: Add observation hook bridge for Codex-compatible environments

**Files:**
- Create: `/Users/felipe_gonzalez/.codex/skills/codex-learning-system/resources/scripts/observe.sh`
- Modify: `/Users/felipe_gonzalez/.codex/skills/codex-learning-system/AGENTS.md`
- Modify: `/Users/felipe_gonzalez/.codex/skills/codex-learning-system/resources/02-learning-loop.md`

**Step 1: Write script contract tests**
Input JSON parsing, truncation, archive rotation behavior.

**Step 2: Implement script**
Store observations with safe fallback for parse errors.

**Step 3: Document integration options**
If Codex hook API exists: direct; else manual/automation ingest pathway.

**Step 4: Commit**
`git commit -m "feat: add observation capture bridge for codex learning"`

## Phase 4: Observer (Optional, staged)

### Task 5: Provide analyzer runner with strict mode boundaries

**Files:**
- Create: `/Users/felipe_gonzalez/.codex/skills/codex-learning-system/resources/scripts/start_observer.sh`
- Create: `/Users/felipe_gonzalez/.codex/skills/codex-learning-system/resources/07-observer-spec.md`

**Step 1: Implement scheduler loop and pid handling**
Start/stop/status.

**Step 2: Add analyzer mode**
Mode A deterministic rules-based extraction (default).
Mode B LLM-assisted extraction (feature-flag).

**Step 3: Add archive behavior**
Move processed observations and create new active file.

**Step 4: Commit**
`git commit -m "feat: add observer runner for instinct extraction"`

## Phase 5: Command UX Parity (`/plan`, `/learn`, `/evolve`)

### Task 6: Enforce plan-before-code policy

**Files:**
- Modify: `/Users/felipe_gonzalez/.codex/skills/codex-learning-system/AGENTS.md`
- Modify: `/Users/felipe_gonzalez/.codex/skills/codex-learning-system/SKILL.md`

**Step 1: Add strict plan mode protocol**
No code changes until explicit confirmation.

**Step 2: Add `/learn` style trigger protocol**
Run after non-trivial solve.

**Step 3: Add `/evolve` cadence**
Run periodic clustering when >=3 related instincts.

**Step 4: Commit**
`git commit -m "docs: enforce plan learn evolve command parity policy"`

## Risks and Mitigations

1. Hook API mismatch in Codex environment
- Mitigation: keep capture decoupled; support manual ingest and automation trigger.

2. Over-generation of low-quality instincts
- Mitigation: min confidence threshold + one-pattern-per-instinct + review gate.

3. Drift between docs and executable scripts
- Mitigation: add smoke tests and example fixtures for each command.

4. Privacy leakage through exported artifacts
- Mitigation: export only distilled instincts, never raw observations.

## Complexity Estimate

- Phase 0-1: Low
- Phase 2-3: Medium
- Phase 4: Medium/High (depending on analyzer strategy)
- Phase 5: Low
- Total: Medium

## Confirmation Gate

Before implementation starts, confirm:
1. Storage root should be `~/.codex/homunculus/` (yes/no)
2. Observer default should be rules-based (yes/no)
3. LLM-assisted extraction should start disabled (yes/no)

## Official Codex Compatibility Addendum (2026-02-13)

### Compatible as planned

- **Skills model and structure**: Official Codex skills support `SKILL.md` with `name` + `description`, optional `scripts/`, `references/`, `assets/`, and optional `agents/openai.yaml`.
- **AGENTS.md policy layering**: Official precedence and merge behavior support plan-level policy controls (`/plan` discipline, overrides by directory).
- **Worktree-first unattended runs**: Codex app automations run in dedicated worktrees for Git repositories, consistent with our isolation model.
- **Unattended automation model**: Official automations run with background safety semantics and default sandbox/approval constraints, compatible with scheduled learning/evolve flows.

### Needs adaptation (not fully compatible as currently written)

- **Hook-based capture bridge (`PreToolUse` / `PostToolUse`)**:
  - This hook model is documented in ECC/Claude ecosystem, but is **not documented as a Codex official extension point** in current Codex docs.
  - Replace Phase 3 default from hook-first to:
    1. `codex exec --json` event ingestion pipeline (officially documented JSONL event stream), and/or
    2. Codex app automations + worktree runs for periodic observation/capture tasks.
  - Keep hook bridge only as optional adapter for non-official environments.

### Path alignment note

- Official Codex docs currently describe skill discovery in `.agents/skills` (repo) and `$HOME/.agents/skills` (user), while this project currently uses `~/.codex/skills`.
- For forward compatibility, support both via:
  - primary write path configurable,
  - optional symlink/mirror strategy,
  - explicit documentation in skill metadata/setup notes.

### Plan patch directives

Apply these modifications before implementation:

1. **Phase 3 rename**:
   - From: Observation hook bridge
   - To: Observation ingest pipeline (official-first: `codex exec --json` + automations)

2. **Phase 3 step rewrite**:
   - Add parser for `codex exec --json` events as canonical event source.
   - Add automation prompt templates for periodic capture jobs in Codex app.
   - Move shell hook adapter to optional appendix.

3. **Phase 1/2 path abstraction**:
   - Add `skills_root` config (`~/.codex/skills` or `~/.agents/skills`) with auto-detection fallback.

4. **Phase 5 command parity clarification**:
   - Use official built-in `/plan` mode + skill invocations.
   - Do not assume plugin-defined custom slash commands.
