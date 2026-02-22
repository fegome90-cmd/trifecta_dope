# Plan First (Use /plan Behavior)

## Objective
Default to a planning-first workflow for any non-trivial task.

## Hard Rules
- For multi-step, risky, or unclear work, start with a concise plan before editing files.
- Treat this as mandatory `/plan` behavior by default.
- Do not jump to implementation until plan steps are clear.

## Plan Format
- Goal
- Constraints
- Steps (ordered)
- Verification commands
- Rollback strategy (if relevant)

## When To Skip Plan
Only skip explicit planning for tiny one-step requests (for example: typo fix, single command output).

## Verification Rule
After implementation, run the planned verification commands and report outcomes.
