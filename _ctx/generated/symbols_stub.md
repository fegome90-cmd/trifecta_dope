# Symbol Navigation - Stub (v1)

> **Status**: Placeholder for symbol-level navigation
> **Version**: v1 (Prime-based) → v2 (AST/LSP-based, planned)
> **Hash**: a199bb667af9

---

## Current Approach (v1)

Symbol navigation uses PRIME index routing via ctx.plan:

- Use `ctx.plan --task "class ClassName"` for class lookup
- Use `ctx.plan --task "function function_name"` for function lookup
- Use `ctx.plan --task "method method_name()"` for method lookup

---

## v2 Roadmap

Planned features for v2 symbol navigation:

1. **AST-based indexing** - Extract all symbols from source
2. **LSP-style features** - Go-to-definition, find references
3. **Cross-references** - Call graphs, dependency analysis

---

**Note**: This stub provides policy guidance. Full symbol indexing requires AST/LSP infrastructure planned for v2.

---

**PROMPT_FIX_HINT**: If you are an agent, copy NEXT_STEPS and rerun the original command. If still failing, paste stderr + command + exit code.
