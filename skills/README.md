# Trifecta Skills

Local skills for Trifecta development and usage.

## Available Skills

### trifecta-global-usage

**Purpose:** Use Trifecta globally from any repository and install it in new projects.

**Features:**
- Global alias setup (bash + fish)
- Repository initialization workflow
- Daemon lifecycle management
- Context search/get workflows
- Troubleshooting guide

**Usage:**
```bash
# Find with skill-hub
skill-hub "trifecta global install setup"

# Or load directly
skill(name="trifecta-global-usage")
```

### runtime-ssot-anchor

**Purpose:** Return to the single Batch 2D runtime SSOT/ancla before trusting derived artifacts or acting on runtime ownership questions.

**Features:**
- Explicit hierarchy (`ADR-004` > repo context > skill)
- Re-entry checklist for handoffs, plans, and reports
- Helper resources under `skills/runtime-ssot-anchor/resources/`

**Usage:**
```bash
# Find with skill-hub after repo indexing/sync
skill-hub "runtime ssot anchor"

# Or load directly
skill(name="runtime-ssot-anchor")
```

## Installation

Skills are automatically indexed by Trifecta's context system. Run:

```bash
trifecta ctx sync --segment .
```

## Adding New Skills

1. Create directory: `skills/skill-name/`
2. Add `SKILL.md` with frontmatter:
   ```yaml
   ---
   name: skill-name
   description: What this skill does
   ---
   ```
3. Run `trifecta ctx sync --segment .`
4. Test: `skill-hub "search query"`

## Skill Structure

```
skills/
├── README.md (this file)
├── trifecta-global-usage/
│   └── SKILL.md
└── runtime-ssot-anchor/
    ├── SKILL.md
    └── resources/
```
