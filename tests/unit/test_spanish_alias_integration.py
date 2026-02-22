"""Test that Spanish aliases work regardless of lint flag state.

This test verifies the decoupling of Spanish alias expansion from the lint flag.
Previously, Spanish alias expansion was gated behind `enable_lint`, causing 22.5%
zero-hit rate for Spanish queries when lint was disabled (default).

TDD Plan:
- Phase 1 (RED): This test should FAIL because Spanish aliases are blocked by enable_lint
- Phase 2 (GREEN): Remove enable_lint condition from Spanish alias expansion
- Phase 3 (REFACTOR): Clean up if needed
- Phase 4: Full test suite verification
"""

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
    tel._ctx_dir = "/tmp/_ctx"
    tel.segment_id = "test-segment"
    tel.segment_label = "test-label"
    return tel


class TestSpanishAliasIndependentOfLint:
    """Spanish alias expansion should work even when lint is disabled."""

    def test_spanish_query_returns_hits_with_lint_disabled(
        self, tmp_path, mock_file_system, mock_telemetry
    ):
        """When lint=False, Spanish queries should still use alias expansion.

        This test verifies the fix for the issue where Spanish alias expansion
        was gated behind the `enable_lint` flag. Spanish aliases should work
        regardless of lint state.

        Scenario:
        1. Search with Spanish term "servicio" returns 0 hits (pass 1)
        2. Spanish alias expands to "service" (pass 2)
        3. Search with "service" returns hits
        4. Result: > 0 hits even though lint is disabled
        """
        # Create minimal segment structure
        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / "aliases.yaml").write_text("aliases: {}")
        (ctx_dir / "context_pack.json").write_text('{"chunks": []}')

        # Mock ContextService to return:
        # - 0 hits for Spanish terms (simulating no match)
        # - 1 hit for English terms (after alias expansion)
        mock_hit = Mock(
            id="chunk-service-1",
            title_path=["service.py"],
            score=0.85,
            token_est=150,
            preview="Service implementation...",
        )

        def mock_search(query, k=10):
            """Return hits only for English terms (after alias expansion)."""
            response = MagicMock()
            # Spanish terms: no hits
            if "servicio" in query.lower():
                response.hits = []
            # English terms: return hits (simulates alias expansion success)
            else:
                response.hits = [mock_hit]
            return response

        with patch(
            "src.application.search_get_usecases.ContextService"
        ) as mock_context_service_class:
            mock_service = Mock()
            mock_service.search = mock_search
            mock_context_service_class.return_value = mock_service

            use_case = SearchUseCase(mock_file_system, mock_telemetry)

            # Execute with Spanish query and lint DISABLED
            result = use_case.execute(
                tmp_path, "servicio", limit=5, enable_lint=False  # Lint DISABLED
            )

            # ASSERT: Should return hits (via Spanish alias expansion), not "No results"
            # This will FAIL before the fix because Spanish alias is gated by enable_lint
            assert "No results" not in result, (
                "Spanish 'servicio' should find hits via alias expansion even with lint disabled. "
                f"Got: {result[:200]}"
            )
            assert "chunk-service-1" in result, (
                f"Expected to find 'service' content via Spanish alias. Got: {result[:200]}"
            )

    def test_spanish_alias_telemetry_emitted_with_lint_disabled(
        self, tmp_path, mock_file_system, mock_telemetry
    ):
        """Spanish alias events should be emitted even when lint is disabled.

        Verifies that telemetry tracks Spanish alias usage independent of lint.
        """
        # Create minimal segment structure
        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / "aliases.yaml").write_text("aliases: {}")
        (ctx_dir / "context_pack.json").write_text('{"chunks": []}')

        mock_hit = Mock(
            id="chunk-config-1",
            title_path=["config.py"],
            score=0.80,
            token_est=100,
            preview="Configuration...",
        )

        def mock_search(query, k=10):
            response = MagicMock()
            # Spanish: no hits
            if "configuración" in query.lower() or "configuracion" in query.lower():
                response.hits = []
            # English: hits
            else:
                response.hits = [mock_hit]
            return response

        with patch(
            "src.application.search_get_usecases.ContextService"
        ) as mock_context_service_class:
            mock_service = Mock()
            mock_service.search = mock_search
            mock_context_service_class.return_value = mock_service

            use_case = SearchUseCase(mock_file_system, mock_telemetry)

            # Execute with Spanish query and lint DISABLED
            use_case.execute(
                tmp_path, "configuración", limit=5, enable_lint=False  # Lint DISABLED
            )

            # ASSERT: Spanish alias telemetry should be recorded
            # Check for spanish_alias event or counter
            incr_calls = [str(call) for call in mock_telemetry.incr.call_args_list]
            event_calls = [str(call) for call in mock_telemetry.event.call_args_list]

            has_spanish_alias_counter = any(
                "spanish_alias" in call for call in incr_calls
            )
            has_spanish_alias_event = any("spanish_alias" in call for call in event_calls)

            assert has_spanish_alias_counter or has_spanish_alias_event, (
                "Spanish alias telemetry should be emitted even with lint disabled. "
                f"incr calls: {incr_calls[:3]}, event calls: {event_calls[:3]}"
            )
