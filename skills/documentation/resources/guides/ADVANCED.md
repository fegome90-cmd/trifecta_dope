# Trifecta Dope - Advanced Guide (30 min)

## Purpose
This guide covers deeper workflows, performance patterns, and operational
requirements. Read Quickstart first.

## 1) Architecture Boundaries
- Domain: pure logic only, no IO, no async
- Application: orchestration and use cases
- Infrastructure: adapters, IO, external services
- Dependencies point inward only

## 2) Context Pack Discipline
- Always run ctx sync before large changes
- Search with instruction-style queries
- Use excerpt mode before raw
- Respect token budgets
- If stale_detected=true: stop, sync, validate

## 3) Session Persistence Protocol
- Append intent before starting
- Log commands used and files touched
- Append result and next step after work
- Keep entries short and factual

## 4) Work Orders (WO)
- Use ctx_wo_take.py to create worktree
- Do all edits inside the worktree
- Commit before finishing WO
- ctx_wo_finish.py validates DoD
- Do not move WO YAML manually

## 5) Testing Strategy
- Unit: tests/unit/
- Integration: tests/integration/
- Acceptance: tests/acceptance/
- Full gate: make gate-all

## 6) Quality Gates
- ruff check
- pyrefly check
- bandit and safety (audit)
- verify.sh (when required by DoD)

## 7) AST and LSP
- LSP daemon runs via UNIX socket and TTL
- Fallback uses AST-only path
- Use ast symbols for structure discovery

## 8) Telemetry
- Telemetry is JSONL in _ctx/telemetry/
- Use telemetry report/chart to review usage
- Avoid side-effects in tests (TRIFECTA_NO_TELEMETRY=1)

## 9) Context Search Patterns
- Bad: "telemetry"
- Good: "Find documentation about telemetry event schema and examples"
- Limit to 1 search + 1 get per turn

## 10) Error Handling
- If ctx validate fails: stop immediately
- If scripts crash: check Makefile shortcuts
- Avoid silent fallback paths

## 11) Documentation Discipline
- Critical warnings must be first
- Keep CLAUDE.md and agents.md aligned
- Use relative paths only
- Do not add absolute paths

## 12) Hooks and Automation
- Hooks live under scripts/hooks
- core.hooksPath points to scripts/hooks
- Disable hooks with TRIFECTA_HOOKS_DISABLE=1

## 13) llms.txt Usage
- llms.txt is the LLM-facing reference
- Keep it structured and low-noise
- Update when core commands or paths change

## 14) Performance Patterns
- Prefer small, focused changes
- Avoid large diffs in a single WO
- Split complex work into multiple WOs

## 15) Review Mindset
- Verify before implementing
- Push back on incorrect assumptions
- Prefer explicit references to files

## 16) Evidence and DoD
- Required artifacts: tests.log, lint.log, diff.patch, handoff.md, verdict.json
- Capture evidence under _ctx/handoff/WO-XXXX/

## 17) Common Pitfalls
- Editing outside worktree
- Skipping ctx sync
- Using absolute paths in docs
- Writing large unstructured plans

## 18) Useful Commands
- make install
- make ctx-sync SEGMENT=.
- make ctx-search Q="instruction" SEGMENT=.
- make gate-all
- uv run trifecta ctx validate --segment .
- uv run trifecta ast symbols "sym://python/mod/src.domain.result"
- uv run trifecta telemetry report -s . --last 30

## 19) Escalation
- If blocked, stop and ask
- If validation fails repeatedly, open a bug
- If docs drift, update llms.txt and CLAUDE.md

## 20) Appendix: Minimal Example Session
1. Append intent in session log
2. Run make ctx-sync SEGMENT=.
3. Search with instruction query
4. Get excerpt
5. Implement change in worktree
6. Run verification commands
7. Append result in session log
