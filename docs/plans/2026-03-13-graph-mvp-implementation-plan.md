# Graph MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a small, testable Trifecta Graph MVP using SegmentRef V1, AST-only indexing, SQLite storage, and a new `trifecta graph` CLI namespace.

**Architecture:** Add a minimal graph slice with simple domain models, a local SQLite store under `.trifecta/cache`, an AST-backed indexer that only uses top-level symbols, a query service for search/callers/callees, and Typer commands wired into the existing CLI. No LSP critical path, no symbol↔chunk linking, no prompt/context generation.

**Tech Stack:** Python 3.12+, Typer, stdlib `sqlite3`, stdlib `ast`, existing `SkeletonMapBuilder`, pytest.

## Task 1: Foundation and RED tests

**Files:**
- Create: `tests/integration/test_graph_store_schema.py`
- Create: `tests/unit/test_graph_indexer.py`
- Create: `tests/integration/cli/test_graph_cli.py`

**Steps:**
1. Write failing tests for SQLite schema init and fail-closed schema versioning.
2. Write failing tests for graph CLI namespace/help and `graph status --json`.
3. Write failing tests for AST indexing, search, callers, and callees on a small fixture.
4. Run the focused tests and confirm they fail for the expected missing-feature reasons.

## Task 2: Minimal graph implementation

**Files:**
- Create: `src/domain/graph_models.py`
- Create: `src/infrastructure/graph_store.py`
- Create: `src/application/graph_indexer.py`
- Create: `src/application/graph_service.py`
- Create: `src/infrastructure/cli_graph.py`
- Modify: `src/infrastructure/cli.py`

**Steps:**
1. Add frozen dataclasses for nodes, edges, status, and CLI-facing results.
2. Implement SQLite schema and CRUD/query methods keyed by `segment_id`.
3. Implement AST-backed indexing for `src/**/*.py` using SegmentRef V1.
4. Add conservative direct-call edge extraction for top-level symbols only.
5. Wire `graph` Typer commands into the main CLI with JSON-first output.

## Task 3: Verification and closeout

**Files:**
- Modify: `_ctx/session_trifecta_dope.md`

**Steps:**
1. Run focused graph tests, then relevant broader verification commands.
2. Update session history with the MVP implementation summary.
3. Review diff for scope discipline.
4. Create one clean commit without `--no-verify`.
