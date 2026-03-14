# Graph MVP Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the reviewed correctness gaps in the Graph MVP without expanding scope beyond the agreed AST-only, SQLite-only, honest-MVP contract.

**Architecture:** Keep the current graph slice and patch it in place. Split read-only graph probing from DB creation, tighten edge extraction so it does not attribute nested calls to top-level symbols, and make callers/callees fail closed when the selector is ambiguous. Do not add LSP, V2 SegmentRef, chunk linking, prompt generation, or richer graph features.

**Tech Stack:** Python 3.12, Typer, stdlib `sqlite3`, stdlib `ast`, pytest.

---

### Task 1: Make read paths non-mutating

**Files:**
- Modify: `src/infrastructure/graph_store.py`
- Modify: `src/application/graph_service.py`
- Modify: `src/infrastructure/cli_graph.py`
- Modify: `tests/unit/test_graph_service.py`
- Modify: `tests/integration/cli/test_graph_cli.py`

**Intent:** `graph status` must not create a DB on a pristine segment. `search`, `callers`, and `callees` must also avoid side effects when no graph index exists yet.

**Steps:**
1. Write a failing unit test in `tests/unit/test_graph_service.py` for a pristine segment:
   - call `GraphService().status(segment)`
   - assert `exists is False`
   - assert `last_indexed_at is None`
   - assert `.trifecta/cache/graph_<segment_id>.db` does not exist after the call
2. Write a failing CLI test in `tests/integration/cli/test_graph_cli.py` for `trifecta graph status --json` on a pristine segment:
   - assert exit code `0`
   - assert `"exists": false`
   - assert no DB file was created
3. Run only those tests and confirm they fail for the current eager-creation behavior.
   - `uv run pytest -q tests/unit/test_graph_service.py tests/integration/cli/test_graph_cli.py`
4. Refactor `src/infrastructure/graph_store.py` so DB creation is explicit:
   - keep schema init for write paths
   - add a read-only status/probe path that can inspect a missing DB without creating it
5. Refactor `src/application/graph_service.py`:
   - `status()` should use the read-only probe
   - `search()`, `callers()`, and `callees()` should return empty results on a missing DB without creating one
6. Keep CLI behavior simple in `src/infrastructure/cli_graph.py`:
   - no new feature surface
   - preserve JSON shape
7. Re-run the focused tests and confirm they pass.
   - `uv run pytest -q tests/unit/test_graph_service.py tests/integration/cli/test_graph_cli.py`

### Task 2: Make edge extraction honest for top-level symbols

**Files:**
- Modify: `src/application/graph_indexer.py`
- Modify: `tests/unit/test_graph_indexer.py`
- Modify: `tests/integration/cli/test_graph_cli.py`

**Intent:** Only direct calls attributable to the top-level symbol should become `calls` edges. Nested defs/classes/lambdas must not leak calls upward to the enclosing top-level function.

**Steps:**
1. Write a failing unit test in `tests/unit/test_graph_indexer.py` with this shape:
   - `root()` contains nested `inner()`
   - `inner()` calls `leaf()`
   - assert `root` has no callees
2. Write a failing CLI regression in `tests/integration/cli/test_graph_cli.py`:
   - index the same fixture
   - assert `trifecta graph callees --symbol root --json` returns an empty list
3. Run the focused tests and confirm they fail.
   - `uv run pytest -q tests/unit/test_graph_indexer.py tests/integration/cli/test_graph_cli.py`
4. Update `src/application/graph_indexer.py`:
   - replace the raw `ast.walk(node)` approach
   - traverse only the executable body owned by the top-level function
   - stop descending into nested `FunctionDef`, `AsyncFunctionDef`, `ClassDef`, and `Lambda`
5. Keep the existing conservative rule set:
   - still only support direct `ast.Name` call targets
   - still only link to known top-level functions from the same file
6. Re-run the focused tests and confirm they pass.
   - `uv run pytest -q tests/unit/test_graph_indexer.py tests/integration/cli/test_graph_cli.py`

### Task 3: Fail closed on ambiguous callers/callees

**Files:**
- Modify: `src/infrastructure/graph_store.py`
- Modify: `src/application/graph_service.py`
- Modify: `src/infrastructure/cli_graph.py`
- Modify: `tests/unit/test_graph_service.py`
- Modify: `tests/integration/cli/test_graph_cli.py`

**Intent:** If a symbol selector matches more than one target node, `callers`/`callees` must not merge results and pretend they are precise.

**Steps:**
1. Write a failing unit test in `tests/unit/test_graph_service.py`:
   - create two files with the same top-level symbol name
   - index both
   - assert `service.callers(segment, "helper")` does not return a merged set
   - choose one safe contract and lock it in:
     - either structured ambiguity error
     - or exception translated by the CLI
2. Write a failing CLI test in `tests/integration/cli/test_graph_cli.py`:
   - invoke `graph callers --symbol helper --json`
   - assert non-zero exit or explicit machine-readable error payload
3. Run the focused tests and confirm they fail.
   - `uv run pytest -q tests/unit/test_graph_service.py tests/integration/cli/test_graph_cli.py`
4. Implement target resolution in `src/infrastructure/graph_store.py`:
   - resolve candidate target nodes first
   - `0 matches` -> empty result
   - `1 match` -> run the relation query
   - `>1 matches` -> raise a typed ambiguity error or a clearly distinguishable exception
5. Translate that outcome in `src/application/graph_service.py` and `src/infrastructure/cli_graph.py`:
   - no silent merging
   - message should include enough data to disambiguate later, such as `file_rel`
6. Re-run the focused tests and confirm they pass.
   - `uv run pytest -q tests/unit/test_graph_service.py tests/integration/cli/test_graph_cli.py`

### Task 4: Decide the JSON-by-default contract explicitly

**Files:**
- Modify: `src/infrastructure/cli_graph.py`
- Modify: `tests/integration/cli/test_graph_cli.py`

**Intent:** Close the contract gap only if we want strict compliance with “machine-readable first”. This is lower priority than the three correctness fixes above.

**Steps:**
1. Decide policy before coding:
   - strict contract: JSON by default, optional `--text`
   - repo-convention exception: keep `--json` opt-in and document the deviation
2. If strict contract is chosen, write a failing CLI test:
   - call `graph status` without `--json`
   - assert JSON output
3. Implement the smallest CLI change in `src/infrastructure/cli_graph.py`.
4. Re-run the CLI tests.
   - `uv run pytest -q tests/integration/cli/test_graph_cli.py`

### Task 5: Final verification and closure

**Files:**
- Modify: `_ctx/session_trifecta_dope.md`

**Steps:**
1. Run the full focused graph suite.
   - `uv run pytest -q tests/integration/test_graph_store_schema.py tests/unit/test_graph_indexer.py tests/unit/test_graph_service.py tests/integration/cli/test_graph_cli.py`
2. Run lint on touched files.
   - `uv run ruff check src/application/graph_indexer.py src/application/graph_service.py src/infrastructure/graph_store.py src/infrastructure/cli_graph.py tests/unit/test_graph_indexer.py tests/unit/test_graph_service.py tests/integration/cli/test_graph_cli.py`
3. Run manual spot checks:
   - pristine `graph status --json`
   - nested-call fixture for `callees`
   - duplicate-symbol fixture for `callers`
4. Append session notes to `_ctx/session_trifecta_dope.md`.
5. Create one clean commit for the review fixes.

## Non-Goals

- Do not redesign node identity beyond what is needed to fail closed on ambiguity.
- Do not add inter-file call resolution.
- Do not add LSP hooks or enrichment.
- Do not touch Graph↔PCC boundaries.
- Do not fold unrelated `_ctx/context_pack.json` hygiene into this fix batch unless it becomes necessary for hooks again.
