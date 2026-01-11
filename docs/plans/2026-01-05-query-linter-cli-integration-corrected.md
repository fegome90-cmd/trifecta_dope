# Query Linter CLI Integration Implementation Plan (CORRECTED)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
>
> **AUDIT NOTE:** This plan has been corrected based on fail-closed audit. Key fixes:
> - Renamed "semantic" to "anchor guidance" (v1 is heuristic, not semantic)
> - Fixed tokenization bug: tokenize AFTER linter, not before
> - Unified config loading from `configs/` (not mixing with `_ctx/`)
> - Use canonical `resolve_segment_root` from `segment_utils.py`
> - Added query sanitization in telemetry
> - Deterministic tests that verify lint_plan directly
> - Added auditable markers for missing config
> - Added feature flag `TRIFECTA_LINT` with conservative default

**Goal:** Integrate Query Linter v1 into `ctx search` command for anchor-based query classification and intelligent expansion of vague queries.

**Architecture:** Two-stage expansion pipeline - Query Linter (anchor guidance layer) → Query Expander (alias layer). The linter classifies queries (vague/semi/guided) using deterministic heuristics (tokens/anchors/aliases) and expands only vague queries with relevant anchors from `configs/anchors.yaml`.

**Tech Stack:** Python 3.12+, Typer CLI, Pydantic, YAML configs, pytest

---

## Current State (Pre-Implementation)

✅ **Query Linter v1 COMPLETE** - All files exist and tested (5/5 tests pass):
- `src/domain/query_linter.py` - Core linter functions (classify, expand, lint)
- `tests/unit/test_query_linter.py` - Unit tests covering all query classes
- `configs/anchors.yaml` - Strong/weak anchor definitions
- `configs/aliases.yaml` - Linter aliases (16 entries, phrase→add_anchors format)
- `docs/reports/query_linter_v1.md` - Complete specification

**Current CLI Search Flow** (`search_get_usecases.py:17-84`):
```python
Normalized Query → Query Expander (aliases) → ContextService → Results
```

**Target Flow** (FIXED - tokenize after linter):
```python
Normalized Query → Query Linter (anchor guidance) → Final Query → Tokenize → Query Expander (aliases) → ContextService → Results
```

---

## Critical Files

| File | Lines | Action |
|------|-------|--------|
| `src/infrastructure/segment_utils.py` | 6-30 | READ - Use existing `resolve_segment_root` |
| `src/infrastructure/config_loader.py` | NEW | CREATE - Load configs/anchors.yaml and configs/aliases.yaml |
| `src/application/search_get_usecases.py` | 17-84 | MODIFY - Add linter integration (FIXED tokenization) |
| `src/infrastructure/cli.py` | 275-303 | MODIFY - Add `--no-lint` flag and `TRIFECTA_LINT` support |
| `tests/unit/test_config_loader.py` | NEW | CREATE - ConfigLoader tests with missing config markers |
| `tests/unit/test_search_usecase_linter.py` | NEW | CREATE - SearchUseCase unit tests (deterministic, verify lint_plan) |
| `tests/integration/test_ctx_search_linter.py` | NEW | CREATE - E2E tests with real context pack (A/B testing) |

---

## Phase 1: Configuration Infrastructure (CORRECTED)

### Task 1.1: Create ConfigLoader with Unified Config Loading

**File:** `src/infrastructure/config_loader.py` (NEW)

**Step 1: Write the failing test**

```python
# tests/unit/test_config_loader.py
import pytest
from pathlib import Path
from src.infrastructure.config_loader import ConfigLoader

def test_load_anchors_existing(tmp_path):
    """Should load anchors.yaml from configs/."""
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    anchors_file = configs_dir / "anchors.yaml"
    anchors_file.write_text("""
anchors:
  strong:
    files:
      - "test.md"
""")
    result = ConfigLoader.load_anchors(tmp_path)
    assert "anchors" in result
    assert "test.md" in result["anchors"]["strong"]["files"]

def test_load_anchors_missing_returns_marker(tmp_path):
    """Should return dict with missing_config marker when anchors.yaml missing."""
    result = ConfigLoader.load_anchors(tmp_path)
    assert result == {"_missing_config": True, "anchors": {}}

def test_load_linter_aliases_existing(tmp_path):
    """Should load linter aliases from configs/aliases.yaml."""
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    aliases_file = configs_dir / "aliases.yaml"
    aliases_file.write_text("""
aliases:
  - phrase: "test phrase"
    add_anchors: ["test.md"]
""")
    result = ConfigLoader.load_linter_aliases(tmp_path)
    assert "aliases" in result
    assert len(result["aliases"]) == 1
    assert result["aliases"][0]["phrase"] == "test phrase"

def test_load_linter_aliases_missing_returns_marker(tmp_path):
    """Should return dict with missing_config marker when aliases.yaml missing."""
    result = ConfigLoader.load_linter_aliases(tmp_path)
    assert result == {"_missing_config": True, "aliases": []}
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/unit/test_config_loader.py::test_load_anchors_existing -v
# Expected: FAIL with "ConfigLoader not defined"
```

**Step 3: Write minimal implementation**

```python
# src/infrastructure/config_loader.py
"""Load YAML configs with graceful error handling and auditable markers."""

from pathlib import Path
from typing import Dict, Any
import yaml

class ConfigLoader:
    """Load YAML configs from repo root configs/."""

    @staticmethod
    def load_anchors(repo_root: Path) -> Dict[str, Any]:
        """Load anchors.yaml from repo_root/configs/.

        Returns dict with "_missing_config: True" marker if missing/invalid.
        This provides auditable visibility vs silent degradation.
        """
        anchors_path = repo_root / "configs" / "anchors.yaml"
        if not anchors_path.exists():
            return {"_missing_config": True, "anchors": {}}
        try:
            with open(anchors_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and "anchors" in data:
                    return data
                return {"_missing_config": True, "anchors": {}}
        except Exception:
            return {"_missing_config": True, "anchors": {}}

    @staticmethod
    def load_linter_aliases(repo_root: Path) -> Dict[str, Any]:
        """Load linter aliases from repo_root/configs/aliases.yaml.

        Returns dict with "_missing_config: True" marker if missing/invalid.
        This is the canonical linter alias format (phrase→add_anchors),
        separate from QueryExpander's _ctx/aliases.yaml (synonym format).
        """
        aliases_path = repo_root / "configs" / "aliases.yaml"
        if not aliases_path.exists():
            return {"_missing_config": True, "aliases": []}
        try:
            with open(aliases_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and "aliases" in data:
                    return data
                return {"_missing_config": True, "aliases": []}
        except Exception:
            return {"_missing_config": True, "aliases": []}
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/unit/test_config_loader.py -v
# Expected: PASS (4/4 tests)
```

**Step 5: Commit**

```bash
git add src/infrastructure/config_loader.py tests/unit/test_config_loader.py
git commit -m "feat: add ConfigLoader with auditable missing_config markers"
```

---

## Phase 2: Core Integration (CORRECTED - Fixed Tokenization Bug)

### Task 2.1: Integrate Linter into SearchUseCase

**File:** `src/application/search_get_usecases.py`
**Lines:** 17-34 (execute method, after normalization, before QueryExpander)

**Current code (lines 27-33):**
```python
# Normalize query
normalized_query = QueryNormalizer.normalize(query)
tokens = QueryNormalizer.tokenize(normalized_query)

# Expand query with aliases
expander = QueryExpander(aliases)
expanded_terms = expander.expand(normalized_query, tokens)
```

**New code (with linter integration - FIXED tokenization order):**
```python
# Normalize query
normalized_query = QueryNormalizer.normalize(query)

# Apply Query Linter (anchor guidance classification + expansion)
# NOTE: We do NOT tokenize yet - tokenization happens AFTER linter decides final query
if enable_lint:
    from src.domain.query_linter import lint_query
    from src.infrastructure.config_loader import ConfigLoader
    from src.infrastructure.segment_utils import resolve_segment_root

    # Use canonical segment_root resolver (not custom _get_repo_root)
    repo_root = resolve_segment_root(target_path)
    anchors_cfg = ConfigLoader.load_anchors(repo_root)
    aliases_cfg = ConfigLoader.load_linter_aliases(repo_root)

    lint_plan = lint_query(normalized_query, anchors_cfg, aliases_cfg)
    query_for_expander = lint_plan["expanded_query"] if lint_plan["changed"] else normalized_query
else:
    # When lint disabled, still create a minimal lint_plan for telemetry consistency
    lint_plan = {
        "query_class": "disabled",
        "token_count": len(normalized_query.split()),
        "anchors_detected": {"strong": [], "weak": [], "aliases_matched": []},
        "changed": False,
        "changes": {"added_strong": [], "added_weak": [], "reasons": []}
    }
    query_for_expander = normalized_query

# NOW tokenize the FINAL query (after linter decision)
# FIX: This was the bug - tokenizing before linter meant tokens didn't match query_for_expander
tokens = QueryNormalizer.tokenize(query_for_expander)

# Expand query with aliases (uses tokens from the CORRECT query)
expander = QueryExpander(aliases)
expanded_terms = expander.expand(query_for_expander, tokens)
```

**Update method signature (line 17):**
```python
def execute(self, target_path: Path, query: str, limit: int = 5, enable_lint: bool = True) -> str:
```

---

### Task 2.2: Add Linter Telemetry (CORRECTED - Sanitized Queries)

**File:** `src/application/search_get_usecases.py`
**Lines:** 50-72 (telemetry section)

**Update telemetry code (after line 64, add linter metrics with query sanitization):**
```python
# Linter telemetry extraction
linter_meta = {
    "query_class": lint_plan.get("query_class", "unknown"),
    "linter_expanded": lint_plan.get("changed", False),
    "linter_added_strong": len(lint_plan.get("changes", {}).get("added_strong", [])),
    "linter_added_weak": len(lint_plan.get("changes", {}).get("added_weak", [])),
    "linter_reasons": lint_plan.get("changes", {}).get("reasons", [])[:3],
    "config_status": "missing" if lint_plan.get("query_class") == "disabled_missing_config" else "ok",
}

# Query sanitization for telemetry (prevent accidental sensitive data leakage)
import hashlib
query_preview = query[:200] if len(query) > 200 else query  # Truncate
query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]  # For correlation without storing raw
query_len = len(query)

# Record telemetry
if self.telemetry:
    self.telemetry.incr("ctx_search_count")
    self.telemetry.incr("ctx_search_hits_total", len(final_hits))
    if len(final_hits) == 0:
        self.telemetry.incr("ctx_search_zero_hits_count")

    # Linter metrics (with visibility when config is missing)
    if lint_plan.get("changed"):
        self.telemetry.incr("ctx_search_linter_expansion_count")
    if lint_plan.get("query_class") == "disabled_missing_config":
        self.telemetry.incr("ctx_search_linter_config_missing_count")
    self.telemetry.incr(f"ctx_search_linter_class_{lint_plan.get('query_class', 'unknown')}_count")

    # Alias expansion metrics
    if expansion_meta["alias_expanded"]:
        self.telemetry.incr("ctx_search_alias_expansion_count")
        self.telemetry.incr("ctx_search_alias_terms_total", expansion_meta["alias_terms_count"])

    # Unified event with SANITIZED query (not raw)
    self.telemetry.event(
        "ctx.search",
        {
            "query_preview": query_preview,
            "query_len": query_len,
            "query_hash": query_hash,
            "limit": limit,
            **expansion_meta,
            **linter_meta,
        },
        {"hits": len(final_hits), "returned_ids": [h.id for h in final_hits]},
        1,
    )
```

**Test:**
```bash
uv run pytest tests/unit/test_search_usecase_linter.py -v
```

**Commit:**
```bash
git add src/application/search_get_usecases.py
git commit -m "feat: integrate Query Linter with fixed tokenization order and sanitized telemetry"
```

---

## Phase 3: CLI Interface (CORRECTED - Added Feature Flag)

### Task 3.1: Add --no-lint Flag and TRIFECTA_LINT Feature Flag

**File:** `src/infrastructure/cli.py`
**Lines:** 275-303 (search command definition)

**Step 1: Add feature flag helper (after imports, around line 20)**

```python
def _get_lint_enabled(no_lint_flag: bool) -> bool:
    """Determine if linting should be enabled based on flag + env var.

    Precedence:
    1. --no-lint flag = True → disabled
    2. TRIFECTA_LINT env var = "0" or "false" → disabled
    3. TRIFECTA_LINT env var = "1" or "true" → enabled
    4. Default: DISABLED (conservative rollout)

    This allows gradual rollout without breaking existing workflows.
    """
    if no_lint_flag:
        return False
    env_val = os.environ.get("TRIFECTA_LINT", "").lower()
    if env_val in ("0", "false", "no"):
        return False
    if env_val in ("1", "true", "yes"):
        return True
    return False  # Conservative default: OFF until explicitly enabled
```

**Step 2: Update search command signature (line 275-281)**

**Current:**
```python
@ctx_app.command("search")
def search(
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    limit: int = typer.Option(5, "--limit", "-l", help="Max results"),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
) -> None:
```

**New:**
```python
@ctx_app.command("search")
def search(
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    limit: int = typer.Option(5, "--limit", "-l", help="Max results"),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
    no_lint: bool = typer.Option(False, "--no-lint", help="Disable query linting (anchor guidance expansion)"),
) -> None:
```

**Step 3: Update docstring (line 282)**

**Current:**
```python
"""Search for relevant chunks in the Context Pack."""
```

**New:**
```python
"""Search for relevant chunks in the Context Pack.

Query Processing Pipeline:
1. Normalization: lowercase, strip, collapse whitespace
2. Linting (optional): anchor-based classification + expansion for vague queries
3. Tokenization: tokenize the FINAL query (post-linter)
4. Alias Expansion: synonym-based expansion using _ctx/aliases.yaml
5. Search: execute weighted search across all terms

Controls:
  --no-lint              Disable linting for this search
  TRIFECTA_LINT=0/1       Env var to enable/disable globally
  Default: DISABLED (conservative rollout)

Use --no-lint or TRIFECTA_LINT=1 to enable.
"""
```

**Step 4: Compute enable_lint and pass to use case (lines 287-290)**

**Current:**
```python
use_case = SearchUseCase(file_system, telemetry)

try:
    output = use_case.execute(Path(segment).resolve(), query, limit=limit)
```

**New:**
```python
use_case = SearchUseCase(file_system, telemetry)

try:
    # Determine if linting should be enabled (conservative default)
    enable_lint = _get_lint_enabled(no_lint)
    output = use_case.execute(Path(segment).resolve(), query, limit=limit, enable_lint=enable_lint)
```

**Test:**
```bash
# Test that --no-lint flag works
TRIFECTA_LINT=1 uv run trifecta ctx search --segment . --query "config"
# Should apply linting (if configs exist)

TRIFECTA_LINT=1 uv run trifecta ctx search --segment . --query "config" --no-lint
# Should skip linting despite env var

TRIFECTA_LINT=0 uv run trifecta ctx search --segment . --query "config"
# Should skip linting
```

**Commit:**
```bash
git add src/infrastructure/cli.py
git commit -m "feat: add --no-lint flag and TRIFECTA_LINT feature flag with conservative default"
```

---

## Phase 4: Testing (CORRECTED - Deterministic Tests)

### Task 4.1: Unit Tests for SearchUseCase (NEW - Deterministic)

**File:** `tests/unit/test_search_usecase_linter.py` (NEW)

**Step 1: Write the failing test**

```python
# tests/unit/test_search_usecase_linter.py
"""Tests for SearchUseCase linter integration (deterministic, verify lint_plan)."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from src.application.search_get_usecases import SearchUseCase

@pytest.fixture
def mock_file_system():
    fs = Mock()
    return fs

@pytest.fixture
def mock_telemetry():
    tel = Mock()
    tel.incr = Mock()
    tel.event = Mock()
    return tel

@pytest.fixture
def mock_context_service():
    """Mock ContextService to return controlled search results."""
    service = Mock()
    # Return hits when searching for "agent.md" or "config"
    mock_hit = Mock(id="chunk1", title_path=["agent.md"], score=0.9, token_est=100, preview="...")
    service.search = Mock(return_value=MagicMock(hits=[mock_hit]))
    return service

def test_linter_expands_vague_query(tmp_path, mock_file_system, mock_telemetry, mock_context_service):
    """Vague query should be expanded by linter (verified via lint_plan)."""
    # Setup: create configs/anchors.yaml in tmp_path
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    anchors_file = configs_dir / "anchors.yaml"
    anchors_file.write_text("""
anchors:
  strong:
    files:
      - "agent.md"
      - "prime.md"
""")

    # Mock ContextService to be injected
    from src.application import context_service
    original_context_service = context_service.ContextService
    context_service.ContextService = Mock(return_value=mock_context_service)

    try:
        use_case = SearchUseCase(mock_file_system, mock_telemetry)

        # Execute with vague query
        # We'll intercept lint_query to verify it was called correctly
        from src.domain import query_linter
        original_lint = query_linter.lint_query
        lint_plan_captured = None

        def mock_lint(*args, **kwargs):
            nonlocal lint_plan_captured
            lint_plan_captured = original_lint(*args, **kwargs)
            return lint_plan_captured

        query_linter.lint_query = mock_lint

        output = use_case.execute(tmp_path, "config", limit=5, enable_lint=True)

        # Verify linter was applied and query was expanded
        assert lint_plan_captured is not None
        assert lint_plan_captured["query_class"] == "vague"
        assert lint_plan_captured["changed"] == True
        assert "agent.md" in lint_plan_captured["expanded_query"] or "prime.md" in lint_plan_captured["expanded_query"]

        # Verify telemetry recorded linter metrics
        assert mock_telemetry.incr.called
        incr_calls = [str(call) for call in mock_telemetry.incr.call_args_list]
        assert any("ctx_search_linter_expansion_count" in call for call in incr_calls)

    finally:
        context_service.ContextService = original_context_service

def test_linter_disabled_with_flag(tmp_path, mock_file_system, mock_telemetry):
    """When enable_lint=False, linter should be skipped."""
    use_case = SearchUseCase(mock_file_system, mock_telemetry)

    # We'll intercept lint_query to verify it was NOT called
    from src.domain import query_linter
    original_lint = query_linter.lint_query
    lint_call_count = [0]

    def mock_lint(*args, **kwargs):
        lint_call_count[0] += 1
        return original_lint(*args, **kwargs)

    query_linter.lint_query = mock_lint

    output = use_case.execute(tmp_path, "config", limit=5, enable_lint=False)

    # Verify linter was NOT called
    assert lint_call_count[0] == 0

def test_guided_query_not_expanded(tmp_path, mock_file_system, mock_telemetry):
    """Guided query should not be expanded (verified via lint_plan)."""
    # Setup configs
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    anchors_file = configs_dir / "anchors.yaml"
    anchors_file.write_text("""
anchors:
  strong:
    files:
      - "agent.md"
""")

    from src.domain import query_linter
    original_lint = query_linter.lint_query
    lint_plan_captured = None

    def mock_lint(*args, **kwargs):
        nonlocal lint_plan_captured
        lint_plan_captured = original_lint(*args, **kwargs)
        return lint_plan_captured

    query_linter.lint_query = mock_lint

    use_case = SearchUseCase(mock_file_system, mock_telemetry)
    output = use_case.execute(tmp_path, "agent.md template creation code file", limit=5, enable_lint=True)

    # Verify: guided query, not expanded
    assert lint_plan_captured["query_class"] == "guided"
    assert lint_plan_captured["changed"] == False
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/unit/test_search_usecase_linter.py::test_linter_expands_vague_query -v
# Expected: FAIL (test setup incomplete)
```

**Step 3: Implement test setup and run**

```bash
# After fixing test setup, run all:
uv run pytest tests/unit/test_search_usecase_linter.py -v
# Expected: PASS (3/3 tests)
```

**Step 4: Commit**

```bash
git add tests/unit/test_search_usecase_linter.py
git commit -m "test: add deterministic SearchUseCase linter integration tests"
```

---

### Task 4.2: Integration Tests (CORRECTED - Real Context Pack, A/B Testing)

**File:** `tests/integration/test_ctx_search_linter.py` (NEW)

```python
"""Integration tests for ctx search with linter (A/B testing with real context pack)."""

import pytest
from pathlib import Path
import tempfile
import yaml
from typer.testing import CliRunner
from src.infrastructure.cli import app

runner = CliRunner()

def _create_minimal_segment(segment_path: Path, include_chunks: bool = True):
    """Helper to create a minimal segment with configs and context pack."""
    # Create configs/
    configs_dir = segment_path / "configs"
    configs_dir.mkdir()
    (configs_dir / "anchors.yaml").write_text("""
anchors:
  strong:
    files:
      - "agent.md"
      - "prime.md"
      - "session.md"
""")
    (configs_dir / "aliases.yaml").write_text("""
aliases:
  - phrase: "session persistence"
    add_anchors: ["session.md", "session append"]
""")

    # Create _ctx/
    ctx_dir = segment_path / "_ctx"
    ctx_dir.mkdir()

    if include_chunks:
        # Create minimal context pack with agent.md and session.md chunks
        chunks = [
            {
                "id": "chunk1",
                "file_path": "agent.md",
                "title": "Agent Documentation",
                "text": "This is the agent.md file with important information. It contains configuration and setup instructions.",
            },
            {
                "id": "chunk2",
                "file_path": "session.md",
                "title": "Session Persistence Protocol",
                "text": "This is session.md with the persistence protocol and session append commands.",
            },
        ]
        (ctx_dir / "context_pack.json").write_text(yaml.dump({"chunks": chunks}))

class TestCtxSearchLinterIntegration:
    """End-to-end tests for query linting with A/B testing."""

    def test_vague_query_with_lint_produces_hits(self, tmp_path):
        """A/B Test: Vague query WITH lint should produce hits (agent.md/prime.md added)."""
        _create_minimal_segment(tmp_path, include_chunks=True)

        # WITH linting (enabled via env var)
        result = runner.invoke(
            app,
            ["ctx", "search", "--segment", str(tmp_path), "--query", "config"],
            env={"TRIFECTA_LINT": "1"},
        )

        # Should find hits because linter added "agent.md" to query
        assert result.exit_code == 0
        assert "chunk1" in result.output or "agent.md" in result.output  # Found agent.md

    def test_vague_query_without_lint_zero_hits(self, tmp_path):
        """A/B Test: Vague query WITHOUT lint should produce zero hits."""
        _create_minimal_segment(tmp_path, include_chunks=True)

        # WITHOUT linting (default or explicit)
        result = runner.invoke(
            app,
            ["ctx", "search", "--segment", str(tmp_path), "--query", "config"],
            env={"TRIFECTA_LINT": "0"},  # Explicitly disabled
        )

        # Should NOT find hits because "config" alone doesn't match any chunk
        assert result.exit_code == 0
        assert "No results found" in result.output or "0 hits" in result.output

    def test_no_lint_flag_overrides_env_var(self, tmp_path):
        """--no-lint flag should override TRIFECTA_LINT=1."""
        _create_minimal_segment(tmp_path, include_chunks=True)

        # Env var says enable, but flag says disable
        result = runner.invoke(
            app,
            ["ctx", "search", "--segment", str(tmp_path), "--query", "config", "--no-lint"],
            env={"TRIFECTA_LINT": "1"},
        )

        # Flag wins: should NOT find hits
        assert result.exit_code == 0
        assert "No results found" in result.output or "0 hits" in result.output

    def test_guided_query_unchanged_by_lint(self, tmp_path):
        """Guided query should not be expanded (lint recognizes it's guided)."""
        _create_minimal_segment(tmp_path, include_chunks=True)

        # Already specific: "agent.md template"
        result = runner.invoke(
            app,
            ["ctx", "search", "--segment", str(tmp_path), "--query", "agent.md template"],
            env={"TRIFECTA_LINT": "1"},
        )

        # Should find hits (agent.md matches) but linter didn't change anything
        assert result.exit_code == 0
        assert "chunk1" in result.output or "agent.md" in result.output

    def test_missing_config_produces_auditable_marker(self, tmp_path):
        """Missing configs should produce auditable marker in telemetry/lint_plan."""
        # Create segment WITHOUT configs/
        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / "context_pack.json").write_text(yaml.dump({"chunks": []}))

        result = runner.invoke(
            app,
            ["ctx", "search", "--segment", str(tmp_path), "--query", "config"],
            env={"TRIFECTA_LINT": "1"},
        )

        # Should NOT crash, and should record missing config
        assert result.exit_code == 0

        # Check telemetry file for marker
        telemetry_file = tmp_path / "_ctx" / "telemetry" / "ctx.search.jsonl"
        if telemetry_file.exists():
            import json
            with open(telemetry_file) as f:
                for line in f:
                    event = json.loads(line)
                    if event.get("args", {}).get("query_class") == "disabled_missing_config":
                        return  # Success: auditable marker found
        pytest.fail("Expected to find disabled_missing_config marker in telemetry")
```

**Test:**
```bash
uv run pytest tests/integration/test_ctx_search_linter.py -v -s
# Expected: PASS (5/5 tests with real context pack A/B testing)
```

**Commit:**
```bash
git add tests/integration/test_ctx_search_linter.py
git commit -m "test: add integration tests with real context pack A/B testing"
```

---

## Phase 5: Documentation (CORRECTED - Removed "Semantic" Language)

### Task 5.1: Update Query Linter Report

**File:** `docs/reports/query_linter_v1.md`

**Add section at end:**
```markdown
## CLI Integration (Phase 4)

**Status**: ✅ INTEGRATED (2026-01-05)

### What This Actually Does
- **NOT "semantic"**: v1 uses deterministic heuristics (tokens/anchors/aliases), not NLP semantics
- **Anchor Guidance**: Classifies queries by anchor density and expands vague ones
- **Goal**: Reduce zero-hits by adding relevant anchors (agent.md, prime.md, docs/)

### Integration Point
- **File**: `src/application/search_get_usecases.py:29-50`
- **Location**: Between QueryNormalizer and QueryExpander
- **Key Fix**: Tokenize AFTER linter (tokens must match final query)

### Configuration Loading (UNIFIED)
- **Anchors**: `configs/anchors.yaml` (repo root, NOT segment-specific)
- **Aliases**: `configs/aliases.yaml` (repo root, linter format)
- **QueryExpander**: Still uses `_ctx/aliases.yaml` (synonym format, separate)

### CLI Flags & Env Vars
- `--no-lint`: Disable linting for this search
- `TRIFECTA_LINT=0/1`: Env var to control default (0=off, 1=on)
- **Default**: DISABLED (conservative rollout until explicitly enabled)

### Telemetry (Sanitized)
- `query_preview[:200]`: Truncated query (not raw)
- `query_hash`: SHA256 for correlation
- `query_len`: For analytics
- `config_status`: "ok" or "missing" (auditable)

### Examples

#### Vague Query (With Expansion) - When Enabled
```bash
$ TRIFECTA_LINT=1 trifecta ctx search --segment . --query "config"
# Internally: normalized → linter (vague) → "config agent.md prime.md" → tokenize → expand
# Query class: vague, expanded: true
```

#### Guided Query (No Expansion)
```bash
$ TRIFECTA_LINT=1 trifecta ctx search --segment . --query "agent.md template creation code"
# Query class: guided (5+ tokens, has strong anchor), expanded: false
```

#### Disabled (Default)
```bash
$ trifecta ctx search --segment . --query "config"
# Linter skipped by default (TRIFECTA_LINT not set)
# Same behavior as before integration
```

### Rollout Strategy
1. **Phase 1** (current): Default OFF, opt-in via `TRIFECTA_LINT=1`
2. **Phase 2**: Monitor telemetry for zero-hit reduction
3. **Phase 3**: If successful, consider default ON in future version
```

**Commit:**
```bash
git add docs/reports/query_linter_v1.md
git commit -m "docs: update Query Linter report with corrected integration details (no 'semantic' language, conservative default)"
```

---

### Task 5.2: Create Integration Guide

**File:** `docs/query-linter-integration.md` (NEW)

```markdown
# Query Linter Integration Guide

## Overview

The Query Linter enhances `ctx search` by applying **anchor-based guidance** (deterministic heuristics) to classify and expand vague queries.

**Important:** This is NOT semantic/NLP analysis. It's deterministic classification using token counts and anchor matching.

## Processing Flow (CORRECTED)

```
Raw Query
    ↓
QueryNormalizer (lowercase, strip)
    ↓
QueryLinter (classify + expand if vague) ← uses configs/anchors.yaml
    ↓
Final Query Decision
    ↓
QueryNormalizer (tokenize FINAL query) ← FIX: was before linter
    ↓
QueryExpander (alias expansion) ← uses _ctx/aliases.yaml
    ↓
ContextService (search)
    ↓
Results
```

## Query Classes

- **Vague** (tokens < 3 OR no anchors): Expands with default entrypoints
- **Semi** (3-4 tokens, some anchors): No expansion
- **Guided** (5+ tokens, 1+ strong anchor): No expansion

## Configuration

### Unified Config Loading

All linter configs come from `configs/` at repository root:

```yaml
# configs/anchors.yaml
anchors:
  strong:
    files: [agent.md, session.md, skill.md, prime.md]
    dirs: [docs/, src/]
  weak:
    intent_terms: [template, doc, docs, guide]
```

```yaml
# configs/aliases.yaml (LINTER format)
aliases:
  - phrase: "session persistence"
    add_anchors: ["session.md", "session append"]
```

### Separate: QueryExpander Configs

```yaml
# _ctx/aliases.yaml (QueryExpander format - separate)
session_persistence:
  - "session.md"
  - "session append"
```

## Usage

### Enable Linting (Opt-In)

```bash
# Via env var
export TRIFECTA_LINT=1
trifecta ctx search --segment . --query "config"

# Or inline
TRIFECTA_LINT=1 trifecta ctx search --segment . --query "config"
```

### Disable Linting (Default)

```bash
# Default behavior (no env var needed)
trifecta ctx search --segment . --query "config"

# Explicit disable
trifecta ctx search --segment . --query "config" --no-lint
TRIFECTA_LINT=0 trifecta ctx search --segment . --query "config"
```

## Telemetry

### Metrics Tracked

- `ctx_search_linter_expansion_count`: Total expansions
- `ctx_search_linter_class_vague_count`
- `ctx_search_linter_class_semi_count`
- `ctx_search_linter_class_guided_count`
- `ctx_search_linter_config_missing_count`: Auditable marker

### Query Sanitization

- `query_preview[:200]`: Truncated (not raw query)
- `query_hash`: SHA256 for correlation
- `query_len`: For analytics

## Troubleshooting

### Linter Not Expanding

1. Check enabled: `echo $TRIFECTA_LINT` (should be "1")
2. Check configs exist: `ls configs/anchors.yaml configs/aliases.yaml`
3. Check telemetry: `cat _ctx/telemetry/ctx.search.jsonl | jq '.args.config_status'`

### Expansion Too Aggressive

- Review `configs/anchors.yaml` strong/weak terms
- Adjust weak intent_terms if over-matching
- Use `--no-lint` for specific queries

### Config Not Loading

- Verify `configs/anchors.yaml` in repository root (NOT segment)
- Check YAML syntax: `python3 -c "import yaml; yaml.safe_load(open('configs/anchors.yaml'))"`
- Check telemetry for `config_status: "missing"`
```

**Commit:**
```bash
git add docs/query-linter-integration.md
git commit -m "docs: add integration guide with corrected terminology and rollout strategy"
```

---

## Phase 6: Verification (CORRECTED)

### Task 6.1: Run All Tests

```bash
# Unit tests
uv run pytest tests/unit/ -v

# Integration tests
uv run pytest tests/integration/ -v

# Acceptance tests
uv run pytest tests/acceptance/ -v

# Full gate
make gate-all
```

**Expected:** All tests PASS

### Task 6.2: Manual Testing (A/B Testing)

```bash
# Setup: In a real segment with configs/
cd /path/to/segment

# Test 1: Vague query WITH linting (should find agent.md/prime.md)
TRIFECTA_LINT=1 uv run trifecta ctx search --segment . --query "config"
# Expected: hits include agent.md or prime.md

# Test 2: Vague query WITHOUT linting (zero hits expected)
TRIFECTA_LINT=0 uv run trifecta ctx search --segment . --query "config"
# Expected: No results found (query too vague)

# Test 3: Guided query (should NOT be expanded)
TRIFECTA_LINT=1 uv run trifecta ctx search --segment . --query "agent.md template code"
# Expected: hits, but query unchanged by linter

# Test 4: Check telemetry for sanitization
cat _ctx/telemetry/ctx.search.jsonl | jq '.args | {query_preview, query_len, query_hash, config_status}'
# Expected: preview truncated, hash present, no raw sensitive data
```

### Task 6.3: Verify Conservative Default

```bash
# Without TRIFECTA_LINT set, linter should be OFF
uv run trifecta ctx search --segment . --query "config"
# Expected: Same behavior as before integration (linter disabled)
```

**Commit final:**
```bash
git add .
git commit -m "feat: complete Query Linter CLI integration (corrected) with conservative default and A/B testing"
```

---

## Success Criteria (CORRECTED)

- [ ] All tests pass (unit, integration, acceptance)
- [ ] Vague queries WITH linting show improved results (A/B test demonstrates this)
- [ ] Vague queries WITHOUT linting show zero hits (control group)
- [ ] Guided queries unchanged regardless of linting
- [ ] `TRIFECTA_LINT=1` enables linting
- [ ] `--no-lint` flag overrides env var
- [ ] Linter metrics appear in telemetry with sanitized queries
- [ ] Missing config produces auditable `disabled_missing_config` marker
- [ ] No performance regression (<50ms overhead)
- [ ] Documentation updated (removed "semantic" language)
- [ ] **Conservative default OFF verified** (no breaking change)

---

## Rollback Plan (ENHANCED)

If issues arise:
1. **Immediate**: Set `TRIFECTA_LINT=0` globally to disable
2. **Revert commits**: Revert `search_get_usecases.py` and `cli.py` changes
3. **Keep**: ConfigLoader and tests (harmless, useful for future)
4. **Monitor**: Check telemetry for `config_status: "missing"` to diagnose config issues

---

## Estimated Timeline (CORRECTED)

- Phase 1 (Config): 45 min (added missing config markers)
- Phase 2 (Core Integration): 2.5 hours (FIXED tokenization order)
- Phase 3 (CLI): 45 min (added feature flag)
- Phase 4 (Testing): 3 hours (deterministic tests + A/B testing)
- Phase 5 (Documentation): 1.25 hours (corrected terminology)
- Phase 6 (Verification): 45 min (verify conservative default)

**Total: ~8.5 hours** (increased due to fixes and proper testing)

---

## Key Fixes Applied

| Issue | Fix | Impact |
|-------|-----|--------|
| "Semantic" misnomer | Renamed to "anchor guidance" | Prevents incorrect assumptions |
| Tokenization bug | Tokenize AFTER linter | Fixes query/expander mismatch |
| Config source mixing | Unified to `configs/` | Single source of truth |
| Custom `_get_repo_root` | Use `resolve_segment_root` | Uses canonical resolver |
| Raw query in telemetry | Sanitize (preview/hash/len) | Prevents sensitive data leakage |
| Flaky tests | Deterministic + A/B testing | Tests validate actual behavior |
| Silent config missing | Auditable markers | Visibility when disabled |
| Default ON (risky) | Default OFF with feature flag | Conservative rollout |
