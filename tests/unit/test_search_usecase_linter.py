"""Tests for SearchUseCase linter integration (deterministic, verify lint_plan)."""

import pytest
from unittest.mock import Mock, MagicMock, patch
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


def test_linter_expands_vague_query(
    tmp_path, mock_file_system, mock_telemetry, mock_context_service
):
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

    # Create _ctx/aliases.yaml (required by AliasLoader)
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    (ctx_dir / "aliases.yaml").write_text("aliases: {}")

    # Create minimal context_pack.json
    (ctx_dir / "context_pack.json").write_text('{"chunks": []}')

    # Mock ContextService to be injected
    with patch(
        "src.application.search_get_usecases.ContextService", return_value=mock_context_service
    ):
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

        use_case.execute(tmp_path, "config", limit=5, enable_lint=True)

        # Verify linter was applied and query was expanded
        assert lint_plan_captured is not None
        assert lint_plan_captured["query_class"] == "vague"
        assert lint_plan_captured["changed"]
        assert (
            "agent.md" in lint_plan_captured["expanded_query"]
            or "prime.md" in lint_plan_captured["expanded_query"]
        )

        # Verify telemetry recorded linter metrics
        assert mock_telemetry.incr.called
        incr_calls = [str(call) for call in mock_telemetry.incr.call_args_list]
        assert any("ctx_search_linter_expansion_count" in call for call in incr_calls)


def test_linter_disabled_with_flag(tmp_path, mock_file_system, mock_telemetry):
    """When enable_lint=False, linter should be skipped."""
    # Create minimal segment
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    (ctx_dir / "aliases.yaml").write_text("aliases: {}")
    (ctx_dir / "context_pack.json").write_text('{"chunks": []}')

    with patch("src.application.search_get_usecases.ContextService"):
        use_case = SearchUseCase(mock_file_system, mock_telemetry)

        # We'll intercept lint_query to verify it was NOT called
        from src.domain import query_linter

        original_lint = query_linter.lint_query
        lint_call_count = [0]

        def mock_lint(*args, **kwargs):
            lint_call_count[0] += 1
            return original_lint(*args, **kwargs)

        query_linter.lint_query = mock_lint

        use_case.execute(tmp_path, "config", limit=5, enable_lint=False)

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

    # Create _ctx
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    (ctx_dir / "aliases.yaml").write_text("aliases: {}")
    (ctx_dir / "context_pack.json").write_text('{"chunks": []}')

    with patch("src.application.search_get_usecases.ContextService"):
        from src.domain import query_linter

        original_lint = query_linter.lint_query
        lint_plan_captured = None

        def mock_lint(*args, **kwargs):
            nonlocal lint_plan_captured
            lint_plan_captured = original_lint(*args, **kwargs)
            return lint_plan_captured

        query_linter.lint_query = mock_lint

        use_case = SearchUseCase(mock_file_system, mock_telemetry)
        use_case.execute(
            tmp_path, "agent.md template creation code file", limit=5, enable_lint=True
        )

        # Verify: guided query, not expanded
        assert lint_plan_captured["query_class"] == "guided"
        assert not lint_plan_captured["changed"]
