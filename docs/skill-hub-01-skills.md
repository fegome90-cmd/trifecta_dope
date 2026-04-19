# Skill-Hub Ecosystem Skills

This document summarizes all skills related to the `skill-hub` ecosystem across different runtimes.

### 1. indexing-skills-safely
- **Source:** pi-agent
- **Path:** `/Users/felipe_gonzalez/.pi/agent/skills/indexing-skills-safely/SKILL.md`
- **Description:** Use when you need to register a skill safely in the global `skill-hub`, refresh a canonical hub entry, or reconcile manifest and count drift with deterministic validation instead of ad-hoc manual indexing.
- **Search hints:** register a skill safely; refresh canonical hub entry; rebuild skills manifest; reconcile searchable skill count; fix skill-hub indexing
- **Key workflow:**
    1. Validate the source `SKILL.md`.
    2. Create or refresh the managed hub entry in `~/.trifecta/segments/skills-hub/`.
    3. Sync the segment using `trifecta ctx sync`.
    4. Rebuild the `skills_manifest.json`.
    5. Verify discovery via `skill-hub`.
- **Scripts:**
    - `audit_skill_hub.py` (13350 bytes)
    - `register_skill.py` (13912 bytes)
    - `bulk_register.sh` (2849 bytes)

```yaml
name: indexing-skills-safely
description: "Use when you need to register a skill safely in the global `skill-hub`, refresh a canonical hub entry, or reconcile manifest and count drift with deterministic validation instead of ad-hoc manual indexing."
search_hints: register a skill safely; refresh canonical hub entry; rebuild skills manifest; reconcile searchable skill count; fix skill-hub indexing
metadata:
  triggers:
    - "register"
    - "a"
    - "skill"
    - "safely;"
    - "refresh"
  role: specialist
  scope: implementation
version: 1.0.0
```

```python
# Key script excerpt (register_skill.py)
SOURCE_ROOTS = [
    ("pi-agent-skills", Path("~/.pi/agent/skills").expanduser()),
    ("agents-skills", Path("~/.agents/skills").expanduser()),
    ("claude-skills", Path("~/.claude/skills").expanduser()),
    ("codex-skills", Path("~/.codex/skills").expanduser()),
    ("examen_grado", Path("~/Developer/examen_grado/skills").expanduser()),
    ("skills-fabrik", Path("~/Developer/skills-fabrik/skills").expanduser()),
    ("superpowers-marketplace", Path("~/.claude/plugins/cache/superpowers-marketplace").expanduser()),
]
SOURCE_PRIORITY = {name: index for index, (name, _) in enumerate(SOURCE_ROOTS)}
TRIFECTA_CLI_ROOT = Path("~/Developer/agent_h/trifecta_dope").expanduser()

MANAGED_START = "<!-- managed-by:indexing-skills-safely:start -->"
MANAGED_END = "<!-- managed-by:indexing-skills-safely:end -->"
```

### 2. skill-workflow
- **Source:** pi-agent
- **Path:** `/Users/felipe_gonzalez/.pi/agent/skills/skill-workflow/SKILL.md`
- **Description:** Use for installing external skills from GitHub: clone, analyze, refactor, register in skill-hub. Do NOT use for creating new skills.
- **Search hints:** install skill github onboard import register external skill-hub progressive disclosure trigger test catalog
- **Key workflow:**
    - **Phase 1-2:** Fetch and Analyze (frontmatter, structure).
    - **Phase 3-5:** Refactor (progressive disclosure), Agnosticize (remove vendor terms), Optimize.
    - **Phase 6:** Register in skill-hub (uses `indexing-skills-safely`).
    - **Phase 7-8:** Test triggers and update catalog.
- **Scripts:** (Empty directory)

```yaml
name: skill-workflow
description: "Use for installing external skills from GitHub: clone, analyze, refactor, register in skill-hub. Do NOT use for creating new skills."
search_hints: install skill github onboard import register external skill-hub progressive disclosure trigger test catalog
metadata:
  triggers:
    - "install skill"
    - "import skill"
    - "onboard skill"
    - "register skill"
    - "skill from GitHub"
    - "skill workflow"
  role: specialist
  scope: implementation
version: 1.0.0
```

### 3. skill-hub-repeat
- **Source:** pi-agent
- **Path:** `/Users/felipe_gonzalez/.pi/agent/skills/skill-hub-repeat/SKILL.md`
- **Description:** Use when the user explicitly wants `skill-hub` used on every task and phase of a multi-step workflow, including implementation, review, debugging, verification, commit, push, or PR work.
- **Search hints:** use skill-hub on every task and phase; repeat skill-hub lookup across workflow phases; rerun skill-hub before each new phase
- **Key workflow:**
    - Identify material phases and concrete task boundaries.
    - Run `skill-hub "<current task instruction>"` before EVERY phase/task.
    - Refine queries if results are too generic.
    - Announce skill choice to keep workflow auditable.
- **Scripts:** None

```yaml
name: skill-hub-repeat
description: "Use when the user explicitly wants `skill-hub` used on every task and phase of a multi-step workflow, including implementation, review, debugging, verification, commit, push, or PR work."
search_hints: use skill-hub on every task and phase; repeat skill-hub lookup across workflow phases; rerun skill-hub before each new phase
metadata:
  triggers:
    - "use"
    - "skill-hub"
    - "on"
    - "every"
    - "task"
  role: specialist
  scope: implementation
version: 1.0.0
```

### 4. find-skills
- **Source:** pi-agent
- **Path:** `/Users/felipe_gonzalez/.pi/agent/skills/find-skills/SKILL.md`
- **Description:** Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending...
- **Search hints:** discover install skills npx search ecosystem package capabilities extend
- **Key workflow:**
    - Search using `npx skills find [query]`.
    - Present options to the user with install commands.
    - Install globally using `npx skills add <package> -g -y`.
- **Scripts:** None

```yaml
name: find-skills
description: Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending...
search_hints: discover install skills npx search ecosystem package capabilities extend
metadata:
  triggers:
    - "discover"
    - "install"
    - "skills"
    - "npx"
    - "search"
  role: specialist
  scope: implementation
version: "1.0.0"
```

### 5. skills-hub
- **Source:** claude
- **Path:** `/Users/felipe_gonzalez/.claude/skills/skills-hub/SKILL.md`
- **Description:** Use when searching for skills in the global skills index. Teaches HOW to search effectively. Triggers on: "find skill", "search skills", "skill-hub", "discover skills".
- **Search hints:** search find discover skills hub global index query
- **Key workflow:**
    - Use descriptive phrases for search queries (not single words).
    - Interpret results (Score, Tokens, Preview, Source Path).
    - Access skill content via `Read <source_path>` or `skill(name="...")`.
- **Scripts:** None

```yaml
name: skills-hub
description: Use when searching for skills in the global skills index. Teaches HOW to search effectively. Triggers on: "find skill", "search skills", "skill-hub", "discover skills".
search_hints: search find discover skills hub global index query
metadata:
  triggers: [find skill], [search skills], [skill-hub], [discover skills], [skill search]
  role: specialist
  scope: implementation
version: 2.0.0
```

### 6. indexing-skills-safely (codex)
- **Source:** codex
- **Path:** `/Users/felipe_gonzalez/.codex/skills/indexing-skills-safely/SKILL.md`
- **Description:** Use when adding or updating Codex skills and you need them discoverable in skill-hub quickly, especially when a skill exists on disk but is missing from search, ctx sync alone was not enough, or manual registration feels risky.
- **Search hints:** (None in frontmatter)
- **Key workflow:**
    - Bundled helper: `python3 ~/.codex/skills/indexing-skills-safely/scripts/register_skill.py --skill /path/to/SKILL.md`.
    - Validates frontmatter, infers source, updates segment entry, runs `trifecta ctx sync`.
- **Scripts:**
    - `register_skill.py` (7542 bytes)

```yaml
name: indexing-skills-safely
description: Use when adding or updating Codex skills and you need them discoverable in skill-hub quickly, especially when a skill exists on disk but is missing from search, ctx sync alone was not enough, or manual registration feels risky.
```

```python
# Key script excerpt (register_skill.py)
SOURCE_ROOTS = [
    ("pi-agent-skills", Path("~/.pi/agent/skills").expanduser()),
    ("agents-skills", Path("~/.agents/skills").expanduser()),
    ("claude-skills", Path("~/.claude/skills").expanduser()),
    ("codex-skills", Path("~/.codex/skills").expanduser()),
    ("examen-grado-skills", Path("~/Developer/examen_grado/skills").expanduser()),
]

MANAGED_START = "<!-- managed-by:indexing-skills-safely:start -->"
MANAGED_END = "<!-- managed-by:indexing-skills-safely:end -->"
```

### 7. skill-hub-repeat (codex)
- **Source:** codex
- **Path:** `/Users/felipe_gonzalez/.codex/skills/skill-hub-repeat/SKILL.md`
- **Description:** Use when the user explicitly wants `skill-hub` used repeatedly across a multi-step workflow, across each task, across each phase, or throughout implementation, review, debugging, commit, push, or PR work. Trigger on requests like `usa skill-hub siempre`, `cada task`, `cada fase`, `en todo el workflow`, or `durante todo el PR`.
- **Search hints:** (None in frontmatter)
- **Key workflow:**
    - Run `skill-hub` before EVERY material phase (isolation, design, implementation, testing, commit, etc.) and EVERY concrete task.
    - Write queries as short instructions.
- **Scripts:** None

```yaml
name: skill-hub-repeat
description: Use when the user explicitly wants `skill-hub` used repeatedly across a multi-step workflow, across each task, across each phase, or throughout implementation, review, debugging, commit, push, or PR work. Trigger on requests like `usa skill-hub siempre`, `cada task`, `cada fase`, `en todo el workflow`, or `durante todo el PR`.
```

### 8. checkpoint-codex
- **Source:** codex
- **Path:** `/Users/felipe_gonzalez/.codex/skills/checkpoint-codex/SKILL.md`
- **Description:** Use when the user asks for a checkpoint, handoff, cambio de ventana de contexto, next-agent prompt, session save, or resume card and you need to generate a Codex-style checkpoint, handoff, checklist, and reopen prompt for $checkpoint-resume.
- **Skill-hub context:** Relies on `skill-hub "checkpoint handoff"` to discover context and uses `indexing-skills-safely` patterns for registry.
- **Key workflow:**
    - Gather state (plan, tasks, errors).
    - Run `python3 ~/.codex/skills/checkpoint-codex/scripts/checkpoint_codex.py`.
    - Produces handoff, checklist, and reopen prompt.
- **Scripts:**
    - `checkpoint_codex.py` (10749 bytes)
    - `checkpoint_card_renderer.py` (7260 bytes)

```yaml
name: checkpoint-codex
description: Use when the user asks for a checkpoint, handoff, cambio de ventana de contexto, next-agent prompt, session save, or resume card and you need to generate a Codex-style checkpoint, handoff, checklist, and reopen prompt for $checkpoint-resume.
```

```python
# Key script excerpt (checkpoint_codex.py)
REQUIRED_FIELDS = (
    "name",
    "current_plan",
    "completed_tasks",
    "pending_tasks",
    "pending_errors",
    "next_agent_prompt",
)

def load_template(path: Path) -> Template:
    return Template(path.read_text(encoding="utf-8"))
```

### 9. learned-contract-drift-fail-open-diagnosis
- **Source:** codex
- **Path:** `/Users/felipe_gonzalez/.codex/skills/learned-contract-drift-fail-open-diagnosis/SKILL.md`
- **Description:** Use when a visible bug looks isolated but evidence suggests a deeper family of failures involving contract drift, implicit migrations, fail-open behavior, partial-success reporting, or telemetry and UX that claim success despite real errors.
- **Skill-hub context:** Born from incidents where `skill-hub` appeared broken due to segment-state corruption and weak manifest contracts.
- **Key workflow:**
    - Separate visible symptom from real execution path.
    - Check for contract drift between persisted artifacts and runtime state.
    - Audit fail-open boundaries (ignored errors, partial success).
- **Scripts:** None

```yaml
name: learned-contract-drift-fail-open-diagnosis
description: Use when a visible bug looks isolated but evidence suggests a deeper family of failures involving contract drift, implicit migrations, fail-open behavior, partial-success reporting, or telemetry and UX that claim success despite real errors.
```
