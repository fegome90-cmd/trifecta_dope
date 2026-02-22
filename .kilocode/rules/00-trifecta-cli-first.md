# Trifecta CLI First (Mandatory)

## Objective
Work in this repository using the Trifecta CLI as the primary navigation and context mechanism.

## Mandatory Startup (Any Agent)
- Before any analysis or code change, read `skill.md` and `AGENTS.md` from the main root worktree.
- Do this even when running from `.worktrees/*`.
- Resolve main root with:
  - `MAIN_ROOT="$(git worktree list --porcelain | awk '/^worktree /{print $2}' | grep -v '/\\.worktrees/' | head -n1)"`
- Then load:
  - `cat "$MAIN_ROOT/skill.md"`
  - `cat "$MAIN_ROOT/AGENTS.md"`

## Hard Rules
- DO NOT start by crawling the repo with broad `find`/`ls -R`/bulk reads.
- DO NOT guess architecture from memory.
- ALWAYS prefer Trifecta commands before direct file traversal.

## Required Workflow
1. Run context sync/validation first when needed:
   - `uv run trifecta ctx sync --segment .`
   - `uv run trifecta ctx validate --segment .`
2. Discover docs with instruction-style search:
   - `uv run trifecta ctx search --segment . --query "Find documentation about <task>" --limit 6`
3. Retrieve only necessary chunks:
   - `uv run trifecta ctx get --segment . --ids "<id1>,<id2>" --mode excerpt --budget-token-est 900`
4. For source symbols, use AST commands before wide grep:
   - `uv run trifecta ast symbols "sym://python/mod/<module>" --segment .`

## Fallback Policy
- If Trifecta returns zero hits, refine query (instruction style, in English) and retry.
- Use direct filesystem search only after Trifecta-based discovery is attempted.

## Completion Check
Before claiming completion, include the exact Trifecta commands used and what they returned.
