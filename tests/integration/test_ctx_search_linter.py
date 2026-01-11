"""Integration tests for Query Linter CLI integration with A/B testing.

Tests verify:
1. Linter expands vague queries when enabled
2. Linter is disabled when flag is False
3. Guided queries are not expanded
4. Missing config disables linter gracefully

Tests use deterministic verification (lint_plan structure) rather than
output strings, making them robust to future formatting changes.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.application.search_get_usecases import SearchUseCase


@pytest.fixture
def mock_file_system():
    """Mock FileSystemAdapter."""
    fs = Mock()
    return fs


@pytest.fixture
def mock_telemetry():
    """Mock telemetry client."""
    tel = Mock()
    tel.incr = Mock()
    tel.event = Mock()
    return tel


@pytest.fixture
def mock_context_service():
    """Mock ContextService to return controlled search results."""
    service = Mock()
    # Return hits when searching for common terms
    mock_hit = Mock(
        id="chunk1",
        title_path=["agent.md"],
        score=0.9,
        token_est=100,
        preview="Agent configuration..."
    )
    service.search = Mock(return_value=MagicMock(hits=[mock_hit]))
    return service


@pytest.fixture
def segment_with_configs(tmp_path):
    """Create a test segment with configs/anchors.yaml and configs/aliases.yaml."""
    # Create configs/ directory
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()

    # Create anchors.yaml with strong anchors
    anchors_file = configs_dir / "anchors.yaml"
    anchors_file.write_text("""
anchors:
  strong:
    files:
      - "agent.md"
      - "prime.md"
    dirs:
      - "docs/"
""")

    # Create aliases.yaml for linter
    aliases_file = configs_dir / "aliases.yaml"
    aliases_file.write_text("""
aliases:
  - phrase: "context"
    add_anchors: ["agent.md"]
""")

    # Create _ctx/ directory with required files
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()

    # Create aliases.yaml for AliasLoader (different from linter aliases)
    (ctx_dir / "aliases.yaml").write_text("aliases: {}")

    # Create minimal context_pack.json
    (ctx_dir / "context_pack.json").write_text('{"chunks": []}')

    # Add segment markers (pyproject.toml for resolve_segment_root)
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname = 'test-segment'")

    return tmp_path


@pytest.fixture
def segment_without_configs(tmp_path):
    """Create a test segment WITHOUT configs/anchors.yaml."""
    # Create _ctx/ directory
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()

    # Create minimal _ctx files
    (ctx_dir / "aliases.yaml").write_text("aliases: {}")
    (ctx_dir / "context_pack.json").write_text('{"chunks": []}')

    # Add segment markers
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname = 'test-segment'")

    return tmp_path


def test_vague_query_expansion_with_linter_enabled(
    segment_with_configs, mock_file_system, mock_telemetry, mock_context_service, capsys
):
    """Test that vague query is expanded when linter is enabled.

    Setup:
    - Segment with configs/anchors.yaml containing agent.md and prime.md
    - enable_lint=True

    Verify:
    - lint_plan["query_class"] == "vague"
    - lint_plan["changed"] == True
    - expanded_query includes agent.md or prime.md
    - Telemetry records expansion metrics
    """
    from src.domain import query_linter

    # Capture lint_plan by patching lint_query
    original_lint = query_linter.lint_query
    lint_plan_captured = None

    def mock_lint(*args, **kwargs):
        nonlocal lint_plan_captured
        lint_plan_captured = original_lint(*args, **kwargs)
        return lint_plan_captured

    query_linter.lint_query = mock_lint

    # Mock ContextService to be injected
    with patch('src.application.search_get_usecases.ContextService', return_value=mock_context_service):
        use_case = SearchUseCase(mock_file_system, mock_telemetry)

        # Execute with vague query (single token, no anchors)
        _ = use_case.execute(
            segment_with_configs,
            "config",  # Vague query: 1 token, no anchors
            limit=5,
            enable_lint=True
        )

        # Verify: linter was applied and query was expanded
        assert lint_plan_captured is not None, "lint_query should have been called"
        assert lint_plan_captured["query_class"] == "vague", \
            f"Expected 'vague', got '{lint_plan_captured['query_class']}'"
        assert lint_plan_captured["changed"] is True, \
            "Query should have been expanded for vague query"

        # Verify: expanded_query includes strong anchors
        expanded_query = lint_plan_captured["expanded_query"]
        assert "agent.md" in expanded_query or "prime.md" in expanded_query, \
            f"Expanded query should include strong anchors: {expanded_query}"

        # Verify: telemetry recorded linter expansion
        assert mock_telemetry.incr.called
        incr_calls = [str(call) for call in mock_telemetry.incr.call_args_list]
        assert any("ctx_search_linter_expansion_count" in call for call in incr_calls), \
            "Telemetry should record linter expansion"

        # Verify: telemetry event includes linter metadata
        assert mock_telemetry.event.called
        event_call = mock_telemetry.event.call_args_list[0]
        event_metadata = event_call[0][1] if event_call[0] else {}
        assert "linter_query_class" in event_metadata
        assert event_metadata["linter_query_class"] == "vague"
        assert event_metadata["linter_expanded"] is True

    # Restore original function
    query_linter.lint_query = original_lint


def test_vague_query_no_expansion_with_linter_disabled(
    segment_with_configs, mock_file_system, mock_telemetry, mock_context_service
):
    """Test that vague query is NOT expanded when linter is disabled.

    Setup:
    - Segment with configs/anchors.yaml
    - enable_lint=False

    Verify:
    - lint_plan["query_class"] == "disabled"
    - lint_plan["changed"] == False
    - expanded_query equals original normalized_query
    - Telemetry records disabled state
    """
    from src.domain import query_linter

    # Verify lint_query is NOT called
    original_lint = query_linter.lint_query
    lint_call_count = [0]

    def mock_lint(*args, **kwargs):
        lint_call_count[0] += 1
        return original_lint(*args, **kwargs)

    query_linter.lint_query = mock_lint

    with patch('src.application.search_get_usecases.ContextService', return_value=mock_context_service):
        use_case = SearchUseCase(mock_file_system, mock_telemetry)

        # Execute with linter disabled
        _ = use_case.execute(
            segment_with_configs,
            "config",
            limit=5,
            enable_lint=False
        )

        # Verify: lint_query was NOT called (optimization)
        assert lint_call_count[0] == 0, \
            f"lint_query should not be called when disabled, but was called {lint_call_count[0]} times"

        # Verify: telemetry records disabled state
        assert mock_telemetry.event.called
        event_call = mock_telemetry.event.call_args_list[0]
        event_metadata = event_call[0][1] if event_call[0] else {}
        assert "linter_query_class" in event_metadata
        assert event_metadata["linter_query_class"] == "disabled"
        assert event_metadata["linter_expanded"] is False

    # Restore original function
    query_linter.lint_query = original_lint


def test_guided_query_not_expanded(
    segment_with_configs, mock_file_system, mock_telemetry, mock_context_service
):
    """Test that guided query is NOT expanded.

    Setup:
    - Segment with configs/anchors.yaml
    - Query: "agent.md template creation code file" (guided query)

    Verify:
    - lint_plan["query_class"] == "guided"
    - lint_plan["changed"] == False
    - No expansion occurs
    - Telemetry records guided classification
    """
    from src.domain import query_linter

    # Capture lint_plan
    original_lint = query_linter.lint_query
    lint_plan_captured = None

    def mock_lint(*args, **kwargs):
        nonlocal lint_plan_captured
        lint_plan_captured = original_lint(*args, **kwargs)
        return lint_plan_captured

    query_linter.lint_query = mock_lint

    with patch('src.application.search_get_usecases.ContextService', return_value=mock_context_service):
        use_case = SearchUseCase(mock_file_system, mock_telemetry)

        # Execute with guided query (5+ tokens with strong anchor)
        _ = use_case.execute(
            segment_with_configs,
            "agent.md template creation code file",  # Guided: 5 tokens, has agent.md anchor
            limit=5,
            enable_lint=True
        )

        # Verify: guided query, not expanded
        assert lint_plan_captured is not None
        assert lint_plan_captured["query_class"] == "guided", \
            f"Expected 'guided', got '{lint_plan_captured['query_class']}'"
        assert lint_plan_captured["changed"] is False, \
            "Guided query should not be expanded"

        # Verify: expanded_query equals original (no changes)
        assert lint_plan_captured["expanded_query"] == "agent.md template creation code file", \
            "Guided query should remain unchanged"

        # Verify: telemetry does NOT record expansion
        incr_calls = [str(call) for call in mock_telemetry.incr.call_args_list]
        assert not any("ctx_search_linter_expansion_count" in call for call in incr_calls), \
            "Telemetry should not record expansion for guided queries"

    # Restore original function
    query_linter.lint_query = original_lint


def test_missing_config_disables_linter(
    segment_without_configs, mock_file_system, mock_telemetry, mock_context_service, capsys
):
    """Test that missing config disables linter gracefully.

    Setup:
    - Segment WITHOUT configs/anchors.yaml
    - enable_lint=True

    Verify:
    - lint_plan["query_class"] == "disabled_missing_config"
    - No expansion occurs
    - ConfigLoader stderr warning appears
    - Telemetry records missing config state
    """
    from src.domain import query_linter

    # Capture lint_plan
    original_lint = query_linter.lint_query
    lint_plan_captured = None

    def mock_lint(*args, **kwargs):
        nonlocal lint_plan_captured
        lint_plan_captured = original_lint(*args, **kwargs)
        return lint_plan_captured

    query_linter.lint_query = mock_lint

    with patch('src.application.search_get_usecases.ContextService', return_value=mock_context_service):
        use_case = SearchUseCase(mock_file_system, mock_telemetry)

        # Execute with linter enabled but missing config
        _ = use_case.execute(
            segment_without_configs,
            "config",
            limit=5,
            enable_lint=True
        )

        # Verify: missing config disables linter
        assert lint_plan_captured is not None
        assert lint_plan_captured["query_class"] == "disabled_missing_config", \
            f"Expected 'disabled_missing_config', got '{lint_plan_captured['query_class']}'"
        assert lint_plan_captured["changed"] is False, \
            "Query should not be expanded when config is missing"

        # Verify: stderr warning from ConfigLoader
        captured = capsys.readouterr()
        assert "anchors.yaml" in captured.err or "aliases.yaml" in captured.err, \
            "ConfigLoader should log warning to stderr for missing config"

        # Verify: telemetry records missing config
        assert mock_telemetry.event.called
        event_call = mock_telemetry.event.call_args_list[0]
        event_metadata = event_call[0][1] if event_call[0] else {}
        assert "linter_query_class" in event_metadata
        assert event_metadata["linter_query_class"] == "disabled_missing_config"
        assert event_metadata["linter_expanded"] is False

    # Restore original function
    query_linter.lint_query = original_lint


def test_semi_query_classification(
    segment_with_configs, mock_file_system, mock_telemetry, mock_context_service
):
    """Test that semi-guided queries are classified correctly.

    Setup:
    - Segment with configs/anchors.yaml
    - Query: "config agent.md setup" (semi-guided: 3 tokens, 1 strong anchor)

    Verify:
    - lint_plan["query_class"] == "semi"
    - lint_plan["changed"] == False (only vague queries are expanded)
    """
    from src.domain import query_linter

    # Capture lint_plan
    original_lint = query_linter.lint_query
    lint_plan_captured = None

    def mock_lint(*args, **kwargs):
        nonlocal lint_plan_captured
        lint_plan_captured = original_lint(*args, **kwargs)
        return lint_plan_captured

    query_linter.lint_query = mock_lint

    with patch('src.application.search_get_usecases.ContextService', return_value=mock_context_service):
        use_case = SearchUseCase(mock_file_system, mock_telemetry)

        # Execute with semi-guided query
        # Semi: 3 tokens, 1 strong anchor (not < 3, not >= 5 with anchors)
        _ = use_case.execute(
            segment_with_configs,
            "config agent.md setup",  # Semi: 3 tokens, 1 anchor
            limit=5,
            enable_lint=True
        )

        # Verify: semi-guided query, not expanded
        assert lint_plan_captured is not None
        assert lint_plan_captured["query_class"] == "semi", \
            f"Expected 'semi', got '{lint_plan_captured['query_class']}'"
        assert lint_plan_captured["changed"] is False, \
            "Semi-guided query should not be expanded (only vague queries are expanded)"

    # Restore original function
    query_linter.lint_query = original_lint
