# Trifecta Dope - Quickstart (5 min)

## 1) Read These First
- skill.md
- _ctx/prime_trifecta_dope.md
- _ctx/agent_trifecta_dope.md
- _ctx/session_trifecta_dope.md

## 2) Install Dependencies
```bash
make install
```

## 3) Sync Context Pack
```bash
make ctx-sync SEGMENT=.
```

## 4) First Search (Instruction, Not Keyword)
```bash
make ctx-search Q="Find documentation about how ctx sync validates a segment" SEGMENT=.
```

## 5) Read Excerpt
```bash
uv run trifecta ctx get --segment . --ids "<id>" --mode excerpt --budget-token-est 900
```

## 6) Core Rules (Do Not Skip)
- Use instruction-based queries, not keywords
- If ctx validate fails: stop, sync, validate
- Log intent and results in _ctx/session_trifecta_dope.md

## 7) First Task Example
- Objective: Inspect CLI entry points
- Read: src/infrastructure/cli.py
- Confirm: any dependency changes required

## 8) Where To Go Next
- docs/CLI_WORKFLOW.md
- docs/CONTRACTS.md
- skills/documentation/resources/guides/ADVANCED.md

## 9) Troubleshooting
- If you see SEGMENT_NOT_INITIALIZED: run make ctx-sync SEGMENT=.
- If a command fails due to missing module: use uv run python
