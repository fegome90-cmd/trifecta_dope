# ADR-006: _ctx/ Directory Structure Conventions

**Status**: Accepted  
**Date**: 2026-01-06  
**Context**: Session reflection revealed incorrect file placement in `_ctx/logs/` due to unclear conventions.

---

## Decision

**_ctx/ directory structure follows strict conventions**:

- **_ctx/logs/**: ONLY `.log` files (command stdout/stderr). Never `.md` files.
- **Intermediate files**: Use `/tmp/` for temporary `.md` files during session updates.
- **Session append workflow**: Create temp in `/tmp/`, append with `cat`, then cleanup.

## Rationale

1. **Gitignore compliance**: `_ctx/logs/` is ignored. Storing docs there breaks git tracking.
2. **Convention clarity**: `.log` extension signals command output, not content.
3. **Tool compatibility**: Scripts expect logs to be parseable text, not markdown.

## Example (Correct)

```bash
# Correct: Use /tmp/ for intermediate markdown
cat > /tmp/session_entry.md <<'EOF'
## Session entry content
EOF
cat /tmp/session_entry.md >> _ctx/session_trifecta_dope.md
rm /tmp/session_entry.md
```

## Example (Incorrect)

```bash
# WRONG: Never create .md in _ctx/logs/
cat > _ctx/logs/session_entry.md <<'EOF'  # ❌ VIOLATES CONVENTION
...
EOF
```

## Consequences

- Clear separation between logs (command evidence) and content (documentation)
- Prevents spurious files in gitignored directories
- Easier to audit _ctx/ structure (logs vs metadata vs generated)

---

**References**: GEMINI.md, CLAUDE.md (Trifecta _ctx/ Directory Conventions section)
