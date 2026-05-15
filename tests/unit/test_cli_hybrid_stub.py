"""Regression tests for the hybrid dispatcher stub.

Ensures that src.infrastructure.cli_hybrid is importable and that
cli.py callsites gracefully fall back to the normal path when the
hybrid dispatch layer is not fully implemented.
"""

from pathlib import Path


from src.domain.result import Err, is_ok
from src.infrastructure.cli_hybrid import HybridDispatcher


class TestHybridDispatcherStub:
    """The dispatcher is a stub — every call returns Err(...) so callers fall back."""

    def test_stub_importable(self) -> None:
        from src.infrastructure.cli_hybrid import HybridDispatcher

        assert HybridDispatcher is not None

    def test_init_accepts_path(self) -> None:
        d = HybridDispatcher(Path("/tmp"))
        assert d is not None

    def test_call_tool_returns_err_for_every_tool(self) -> None:
        d = HybridDispatcher(Path("/tmp"))
        for tool in ("ctx_search", "ctx_get", "ctx_oracle"):
            result = d.call_tool(tool, {"query": "test"})
            assert result.is_err()
            assert tool in result.unwrap_err()

    def test_err_contains_tool_name(self) -> None:
        d = HybridDispatcher(Path("/tmp"))
        result = d.call_tool("ctx_search", {"query": "test"})
        assert not is_ok(result)
        assert "ctx_search" in result.unwrap_err()

    def test_err_is_not_ok(self) -> None:
        d = HybridDispatcher(Path("/tmp"))
        result = d.call_tool("ctx_search", {})
        assert not is_ok(result)


class TestFallbackMatchesDomainResult:
    """Ensure callers can test .is_ok() exactly as they would for a real Result."""

    def test_stub_is_ok_returns_false(self) -> None:
        d = HybridDispatcher(Path("/tmp"))
        result = d.call_tool("ctx_search", {})
        assert result.is_ok() is False

    def test_stub_is_err_returns_true(self) -> None:
        d = HybridDispatcher(Path("/tmp"))
        result = d.call_tool("ctx_search", {})
        assert result.is_err() is True

    def test_stub_is_ok_type_safe(self) -> None:
        d = HybridDispatcher(Path("/tmp"))
        result = d.call_tool("ctx_search", {})
        assert isinstance(result, Err)
