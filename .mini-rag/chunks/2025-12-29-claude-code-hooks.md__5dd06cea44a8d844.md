## Notes / Assumptions

- Wrapper is the required entry point for Claude Code CLI (fail-closed enforcement).
- CI gate is authoritative for enforcement when local usage is bypassed.
- `session_ast.md` remains append-only; run record entries are the only modification surface.
