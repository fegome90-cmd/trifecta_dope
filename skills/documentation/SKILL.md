---
name: agent-documentation
description: Use when creating or updating agent onboarding files (CLAUDE.md, agents.md, skill.md) to capture LLM attention on critical context with strategic positioning, warning symbols, and explicit consequences
---

# Agent Documentation Skill

## Overview

Agent Documentation ensures critical project context is prominently positioned so LLMs prioritize reading required files before proceeding. The skill uses positional priority, attention-capturing symbols, and explicit consequences to prevent assumptions and architectural violations.

## When to Use

**Situations:**
- Creating/updating CLAUDE.md or agents.md (onboarding files)
- Agents propose features that already exist (missing implementation docs)
- Agents skip reading critical context and make wrong assumptions
- Critical warnings are buried below other content
- Documentation spans multiple files and needs clear read order

## Core Pattern: 4 Layers of Documentation

```
Layer 1: CRITICAL (Position: FIRST) → ⚠️ "DO NOT PROCEED" + Mandatory Files
Layer 2: QUICK START → Copy-paste commands, confidence building
Layer 3: ARCHITECTURE → Design decisions, patterns, constraints
Layer 4: REFERENCE → Lookup tables, troubleshooting, appendix
```

**Layer 1 Key Techniques:**
- Position: First section, before anything else
- Symbols: ⚠️ ⛔ 🛑 warning icons
- Language: "**DO NOT PROCEED**", "**MANDATORY**", "breach of contract"
- Structure: Numbered list (0, 1, 2) with ← arrows + time estimates
- Consequences: Section "If You Skip" with explicit ⛔ failures and ✅ fixes

## Common Mistakes

| Mistake | Why Bad | Fix |
|---------|---------|-----|
| Burying Layer 1 below Quick Start | LLM forms assumptions before reaching critical context | Put CRITICAL section FIRST |
| Passive language ("should read") | Doesn't register as urgent | Use imperatives: "DO NOT PROCEED" |
| Generic descriptions | LLMs skim vague content | Be specific: "Skip → duplicate work, break things" |
| Lowercase warnings | Blends with normal text | Use `## ⚠️ CRITICAL: ALL CAPS` + **bold** |
| No time estimates | LLMs ignore with unknown cost | Add estimates: "← (3 min read)" |
| Unclear consequences | Why read if you don't know what happens? | "Skip → you'll violate patterns, fail gates" |
| Too many context files | Kills attention (10 files = skip all) | Limit to 3-5 files max |
| Stale paths (e.g., /Users/...) | Breaks trust and confuses context | Use relative paths only |

## Implementation

1. **Use templates** → See `resources/CLAUDE_md_template.md` and `resources/agents_md_template.md`
2. **Run verification** → See `resources/verify_documentation.sh`
3. **Review examples** → See `resources/examples/CLAUDE_md_good_vs_bad.md`
4. **Check your work** → See `resources/checklist.md`
5. **Install hooks** → See `scripts/hooks/install-hooks.sh`

## Health Score & Gate Verdict

The validation script provides a health score and gate verdict:

```
Score = 100 - (ERRORS × 15) - (WARNINGS × 5)

Thresholds:
- Score >= 80: PASS
- Score 60-79: WARN
- Score < 60: FAIL

Gate Verdict:
- BLOCK: Any FAIL (or --strict with WARN)
- ALLOW: No FAIL
```

Run with `--json` for machine parsing or `--strict` for CI.

### Gate Verdict Breakdown

The output shows Core vs Overmind signal breakdown:

```
Gate Verdict: BLOCK (6 FAILs)
  └─ Core: 6 FAIL, 1 WARN | Overmind: 0 FAIL, 2 WARN
```

- **Core signals**: CLAUDE.md validation (critical section, time estimates, links, etc.)
- **Overmind signals**: Ownership, ADR, Coverage-Lite (project-level health indicators)

## Overmind Signals (Phase 1)

Optional signals for deeper documentation health checks:

| Signal | Config | What It Checks |
|--------|--------|----------------|
| **Ownership** | `OWNERSHIP_REQUIRED=1` | Docs have owner via CODEOWNERS or frontmatter |
| **ADR** | `ADR_REQUIRED=1` | Architecture Decision Records in docs/adr/ |
| **Coverage-Lite** | Always on (configurable) | docs/src ratio with anti-gaming |

### Ownership Signal

Detects documentation files without explicit owner.

```bash
# Enable
OWNERSHIP_REQUIRED=1 bash verify_documentation.sh . --force

# Or in .env
OWNERSHIP_REQUIRED=1
```

Remediation:
- Add to `.github/CODEOWNERS`: `/docs/* @team-name`
- Or add to doc frontmatter:
  ```yaml
  ---
  owner: @team-name
  ---
  ```

### ADR Signal

Detects Architecture Decision Records and their freshness.

```bash
# Enable (or automatically activates if docs/adr/ exists)
ADR_REQUIRED=1 bash verify_documentation.sh . --force
```

Remediation:
```bash
mkdir -p docs/adr
echo "# ADRs" > docs/adr/README.md
echo "# ADR-001: Use Postgres" > docs/adr/ADR-001-postgres.md
```

### Coverage-Lite Signal

Heuristic ratio of documentation to source code (excludes empty docs, meta-docs).

```bash
# Configure directories
SRC_DIRS="src,lib" DOC_DIRS="docs,api" bash verify_documentation.sh . --force
```

Thresholds:
- < 0.05: WARN (critical gap)
- 0.05-0.1: INFO (low but acceptable)
- >= 0.1: PASS (healthy)

## WO Prohibition

The validation script **prohibits** checking Work Order paths:

```
WO paths always SKIP: _ctx/, _ctx/jobs/, _ctx/backlog/, WO-*.yaml, backlog.yaml
```

This ensures WO contexts are never validated by the documentation skill.

## Git Hook Automation

For automated validation before commits:

```bash
# Install hooks
bash scripts/hooks/install-hooks.sh

# Enable validation (required)
touch .documentation-skill
```

The validation is **opt-in**. Without `.documentation-skill`, it skips silently.

## Resources

All templates, scripts, and examples are in `skills/documentation/resources/`:

```
resources/
├── CLAUDE_md_template.md          # Ready-to-use template
├── agents_md_template.md          # Ready-to-use template
├── skill_md_template.md           # Ready-to-use template
├── verify_documentation.sh        # Validation script (with health score)
├── checklist.md                   # Implementation checklist
├── HOOKS_GUIDE.md                 # Git hooks documentation
├── OVERMIND_SLICE_SPEC.md         # Phase 1 design spec (signals, thresholds)
└── examples/
    └── CLAUDE_md_good_vs_bad.md   # Before/After example

scripts/hooks/
├── install-hooks.sh               # Install git hooks
└── pre-commit                    # Pre-commit validation
```

For quick reference, see `llms.txt` (L0: Quick Reference).

Start with templates, validate with script, check against checklist.
