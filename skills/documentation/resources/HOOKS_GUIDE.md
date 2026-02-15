# Git Hooks Guide

Documentation automation hooks for Trifecta.

---

## What the Hook Does

The pre-commit hook validates documentation before each commit:

1. **Detects doc changes** - Only runs if CLAUDE.md, agents.md, skill.md, llms.txt, or docs/ changed
2. **Validates doc patterns** - Runs verify_documentation.sh (health score >= 80 required)
3. **Syncs context** - Runs `trifecta ctx sync` if uv is available

---

## Installation

```bash
# From repo root
bash scripts/hooks/install-hooks.sh
```

This sets `git config core.hooksPath scripts/hooks`.

---

## Philosophy

### Local/Offline Checks (in pre-commit)
- File structure validation
- CRITICAL section position
- No absolute paths
- Local link validation
- Staleness detection (via git history)

### Online/CI Checks (run manually or in CI)
- External link validation (`--online` flag)
- Full sync with remote services

---

## Usage

### Normal Commit
```bash
git commit -m "feat: add feature"
# Hook runs automatically
```

### Bypass Hook (urgent)
```bash
git commit -m "urgent: fix" --no-verify
```

### Disable Hooks Globally
```bash
TRIFECTA_HOOKS_DISABLE=1 git commit -m "..."
```

---

## Validation Script

The hook uses `verify_documentation.sh` with these flags:

| Flag | Description |
|------|-------------|
| (none) | Local checks only, offline |
| `--online` | Include external link checks |
| `--json` | Machine-readable output |
| `--strict` | Treat warnings as errors |

### Health Score

```
Score = 100 - (ERRORS × 15) - (WARNINGS × 5)

Thresholds:
- PASS:  >= 80
- WARN:  60-79
- FAIL:  < 60
```

---

## Troubleshooting

### Hook blocks commit
```
❌ Documentation validation failed!
```
**Fix**: Run verify manually and fix issues:
```bash
bash skills/documentation/resources/verify_documentation.sh
```

### ctx sync fails
```
⚠️ ctx sync had issues
```
**Fix**: Run manually:
```bash
trifecta ctx sync --segment .
```

### Hook slow
The hook only runs when doc files are staged. For large repos, consider:
- Run verify separately: `bash verify_documentation.sh`
- Use `--no-verify` for small fixes

### "No documentation changes detected"
This is normal. The hook skips validation when only code changes.

---

## Uninstall

```bash
git config --unset core.hooksPath
rm -f scripts/hooks/pre-commit
```

---

## Related

- `skills/documentation/resources/verify_documentation.sh` - Validation script
- `skills/documentation/resources/guides/QUICKSTART.md` - Quick start guide
- `llms.txt` - Quick reference for agents
