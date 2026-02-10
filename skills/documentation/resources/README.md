# Documentation Resources

This directory contains reusable resources for the Agent Documentation skill: templates, scripts, checklists, and examples.

## Quick Start

**To apply the skill to your project:**

1. **Read the skill** → `skills/documentation/SKILL.md` (5 min)
2. **Review example** → `examples/CLAUDE_md_good_vs_bad.md` (3 min)
3. **Copy template** → `CLAUDE_md_template.md` → your `CLAUDE.md`
4. **Customize it** → Fill in project-specific details
5. **Validate** → Run `verify_documentation.sh`
6. **Check** → Use `checklist.md` for final verification

## File Reference

### Templates

Use these to create or update documentation:

- **[CLAUDE_md_template.md](CLAUDE_md_template.md)** - Template for CLAUDE.md (onboarding for Claude)
  - Copy → customize → validate
  - Instructions included in file
  
- **[agents_md_template.md](agents_md_template.md)** - Template for agents.md (onboarding for all agents)
  - Parallel to CLAUDE.md but for external/diverse agents
  - Emphasizes red flags and must-not rules
  - Keep in sync with CLAUDE.md
  
- **[skill_md_template.md](skill_md_template.md)** - Template for skill.md (project rules and patterns)
  - Concise format (100-200 lines max)
  - Use progressive disclosure (complex stuff → `resources/`)

### Validation & Verification

Use these to validate your documentation:

- **[verify_documentation.sh](verify_documentation.sh)** - Automated validation script
  - Run: `bash skills/documentation/resources/verify_documentation.sh`
  - Checks: CRITICAL section, time estimates, paths, consistency, etc.
  - Exit code 0 = all checks passed
  
- **[checklist.md](checklist.md)** - Manual review checklist
  - 30+ items to check before committing
  - Organized by section (Layer 1, Typography, Files, Language, etc.)
  - Use after running script

### Examples & Reference

Learn from these:

- **[examples/CLAUDE_md_good_vs_bad.md](examples/CLAUDE_md_good_vs_bad.md)** - Before/After comparison
  - Shows ❌ BAD onboarding vs ✅ GOOD onboarding
  - Highlights key improvements
  - Real-world example

## Workflow

### New Project

```bash
# 1. Copy template
cp skills/documentation/resources/CLAUDE_md_template.md CLAUDE.md

# 2. Customize for your project (replace [XXX] placeholders)
# Edit CLAUDE.md with your project details

# 3. Validate
bash skills/documentation/resources/verify_documentation.sh

# 4. Manual verification
# Go through checklist.md and check each item

# 5. Commit
git add CLAUDE.md agents.md skill.md
git commit -m "docs: add Agent Documentation Skill"
```

### Update Existing

```bash
# 1. Review current file
cat CLAUDE.md

# 2. Check what's wrong with script
bash skills/documentation/resources/verify_documentation.sh

# 3. Compare to template
diff CLAUDE.md_template.md CLAUDE.md

# 4. Use checklist to identify gaps
# Open checklist.md and audit your file

# 5. Fix issues
# Update CLAUDE.md with corrections

# 6. Re-validate
bash skills/documentation/resources/verify_documentation.sh
```

## Structure

```
skills/documentation/
├── SKILL.md                                    # Main skill (concise, uses progressive disclosure)
├── resources/                                  # All supporting resources
│   ├── CLAUDE_md_template.md                   # Template for CLAUDE.md
│   ├── agents_md_template.md                   # Template for agents.md
│   ├── skill_md_template.md                    # Template for skill.md
│   ├── verify_documentation.sh                 # Bash validation script
│   ├── checklist.md                            # Manual review checklist (30+ items)
│   ├── examples/
│   │   └── CLAUDE_md_good_vs_bad.md            # Before/After comparison
│   └── README.md                               # This file
```

## Key Principles

### Progressive Disclosure
- **SKILL.md**: Concise (200-300 lines), points to resources
- **resources/**: Detailed templates, scripts, examples
- **Agent reads**: Skill first, then uses resources as needed

### Resource-Based Learning
- Don't embed 1000-line guides in SKILL.md
- Move details to separate files agents can reference
- Templates let agents copy/paste (faster)
- Scripts automate validation (fewer mistakes)

### Practical Focus
- Everything is executable or copyable
- Templates have placeholder comments: `[CUSTOMIZE THIS]`
- Script tells you exactly what's wrong
- Checklist confirms before committing

## Contributing

To improve these resources:

1. **Report issues** → Document what's wrong
2. **Test changes** → Run script on your documentation
3. **Update templates** → Keep examples current
4. **Verify examples** → Compare template output vs. example
5. **Update checklist** → Add items if script gains new checks

## References

- **Superpowers**: [writing-skills/SKILL.md](https://github.com/obra/superpowers) - TDD approach to documentation
- **Agent Documentation Skill**: [skills/documentation/SKILL.md](../SKILL.md)
- **Examples**: [CLAUDE.md](../../CLAUDE.md), [agents.md](../../agents.md) - Real implementations
