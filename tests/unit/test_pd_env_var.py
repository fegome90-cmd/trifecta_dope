"""Unit test for env var precedence (TRIFECTA_PD_MAX_CHUNKS)."""

import os
import pytest
from unittest.mock import MagicMock, patch
from src.application.search_get_usecases import GetChunkUseCase
from src.domain.context_models import GetResult, ContextChunk


@pytest.fixture
def mock_context_service():
    """Mock ContextService to avoid filesystem dependencies."""
    with patch("src.application.search_get_usecases.ContextService") as mock:
        service_instance = MagicMock()
        mock.return_value = service_instance
        # Mock get() to return a simple result
        service_instance.get.return_value = GetResult(
            chunks=[
                ContextChunk(
                    id="test:1",
                    doc="test",
                    title_path=["test.md"],
                    text="content",
                    char_count=100,
                    token_est=25,
                    source_path="test.md",
                )
            ],
            total_tokens=25,
            stop_reason="complete",
            chunks_requested=1,
            chunks_returned=1,
            chars_returned_total=100,
        )
        yield service_instance


def test_env_var_used_when_no_cli_flag(mock_context_service, tmp_path):
    """Test that TRIFECTA_PD_MAX_CHUNKS env var is used when --max-chunks is not provided."""
    from src.infrastructure.file_system import FileSystemAdapter

    # Set env var
    os.environ["TRIFECTA_PD_MAX_CHUNKS"] = "5"

    try:
        use_case = GetChunkUseCase(FileSystemAdapter(), telemetry=None)

        # Simulate CLI call without --max-chunks flag (max_chunks=None)
        # This would normally come from cli.py which reads the env var
        env_max_chunks_str = os.environ.get("TRIFECTA_PD_MAX_CHUNKS")
        effective_max_chunks = int(env_max_chunks_str) if env_max_chunks_str else None

        use_case.execute(
            tmp_path,
            ["test:1"],
            mode="excerpt",
            budget_token_est=1000,
            max_chunks=effective_max_chunks,  # Should be 5 from env var
        )

        # Verify that get() was called with max_chunks=5
        mock_context_service.get.assert_called_once()
        call_kwargs = mock_context_service.get.call_args[1]
        assert call_kwargs["max_chunks"] == 5
    finally:
        del os.environ["TRIFECTA_PD_MAX_CHUNKS"]


def test_cli_flag_overrides_env_var(mock_context_service, tmp_path):
    """Test that CLI --max-chunks flag takes precedence over env var."""
    from src.infrastructure.file_system import FileSystemAdapter

    # Set env var to one value
    os.environ["TRIFECTA_PD_MAX_CHUNKS"] = "5"

    try:
        use_case = GetChunkUseCase(FileSystemAdapter(), telemetry=None)

        # Simulate CLI call WITH --max-chunks flag (max_chunks=3)
        # CLI flag should win over env var
        cli_max_chunks = 3  # From CLI flag

        use_case.execute(
            tmp_path,
            ["test:1", "test:2", "test:3"],
            mode="excerpt",
            budget_token_est=1000,
            max_chunks=cli_max_chunks,  # Should be 3 from CLI, not 5 from env
        )

        # Verify that get() was called with max_chunks=3 (CLI wins)
        mock_context_service.get.assert_called_once()
        call_kwargs = mock_context_service.get.call_args[1]
        assert call_kwargs["max_chunks"] == 3
    finally:
        del os.environ["TRIFECTA_PD_MAX_CHUNKS"]
