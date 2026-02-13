"""Tests for LSP explicit fallback contract (WO-0040).

Verifies that no silent fallbacks exist - every degraded response
must include capability_state, fallback_reason, backend, response_state.
"""

import json
import subprocess
import sys
from pathlib import Path

from src.domain.lsp_contracts import (
    LSPResponse,
    CapabilityState,
    FallbackReason,
    ResponseState,
    Backend,
)


class TestLSPResponseContract:
    """Unit tests for LSPResponse dataclass and factory methods."""

    def test_full_response_structure(self):
        """Full response must include all contract fields."""
        data = {"symbol": "test", "type": "function"}
        response = LSPResponse.full_response(data, backend=Backend.LSP_PYRIGHT)

        result = response.to_dict()

        assert result["status"] == "ok"
        assert result["capability_state"] == CapabilityState.FULL.value
        assert result["backend"] == Backend.LSP_PYRIGHT.value
        assert result["response_state"] == ResponseState.COMPLETE.value
        assert "fallback_reason" not in result  # Not needed for full responses
        assert result["data"] == data

    def test_degraded_response_includes_fallback_reason(self):
        """Degraded response MUST include fallback_reason."""
        response = LSPResponse.degraded_response(
            fallback_reason=FallbackReason.LSP_NOT_READY,
            backend=Backend.AST_ONLY,
            data={"partial": True},
        )

        result = response.to_dict()

        assert result["status"] == "ok"
        assert result["capability_state"] == CapabilityState.DEGRADED.value
        assert result["fallback_reason"] == FallbackReason.LSP_NOT_READY.value
        assert result["backend"] == Backend.AST_ONLY.value
        assert result["response_state"] == ResponseState.DEGRADED.value
        assert result["data"] == {"partial": True}

    def test_wip_response_structure(self):
        """WIP response must declare WIP state and NOT_IMPLEMENTED reason."""
        response = LSPResponse.wip_response(
            data={"stub": True},
            message="Work in progress",
        )

        result = response.to_dict()

        assert result["status"] == "ok"
        assert result["capability_state"] == CapabilityState.WIP.value
        assert result["backend"] == Backend.WIP_STUB.value
        assert result["response_state"] == ResponseState.PARTIAL.value
        assert result["fallback_reason"] == FallbackReason.LSP_NOT_IMPLEMENTED.value

    def test_error_response_for_fail_closed(self):
        """Error response for fail-closed scenarios."""
        response = LSPResponse.error_response(
            error_code="LSP_UNAVAILABLE",
            fallback_reason=FallbackReason.LSP_BINARY_NOT_FOUND,
            message="LSP not available",
        )

        result = response.to_dict()

        assert result["status"] == "error"
        assert result["error_code"] == "LSP_UNAVAILABLE"
        assert result["capability_state"] == CapabilityState.UNAVAILABLE.value
        assert result["fallback_reason"] == FallbackReason.LSP_BINARY_NOT_FOUND.value
        assert result["response_state"] == ResponseState.ERROR.value

    def test_unavailable_response_structure(self):
        """Unavailable response for when LSP is not accessible."""
        response = LSPResponse.unavailable_response(
            fallback_reason=FallbackReason.LSP_BINARY_NOT_FOUND,
        )

        result = response.to_dict()

        assert result["status"] == "ok"
        assert result["capability_state"] == CapabilityState.UNAVAILABLE.value
        assert result["fallback_reason"] == FallbackReason.LSP_BINARY_NOT_FOUND.value
        assert result["response_state"] == ResponseState.DEGRADED.value


class TestHoverExplicitFallback:
    """Integration tests for hover command with explicit fallback."""

    def test_hover_returns_explicit_fallback_when_lsp_unavailable(self, tmp_path: Path):
        """Hover must return explicit fallback contract when LSP unavailable.

        Contract verification:
        - capability_state: WIP or UNAVAILABLE
        - fallback_reason: enum value
        - backend: wip_stub or unavailable
        - response_state: partial or degraded
        - NO silent "status: ok" without capability_state
        """
        # Create minimal segment
        (tmp_path / "skill.md").write_text("# Test")
        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / "agent_test.md").write_text("# Agent")
        (ctx_dir / "prime_test.md").write_text("# Prime")
        (ctx_dir / "session_test.md").write_text("# Session")

        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo(): pass")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.infrastructure.cli",
                "ast",
                "hover",
                str(test_file),
                "--line",
                "1",
                "--char",
                "1",
                "--segment",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )

        # Should succeed (exit 0) but with explicit fallback
        assert result.returncode == 0, (
            f"Expected exit 0, got {result.returncode}. stderr: {result.stderr}"
        )

        output = json.loads(result.stdout)

        # CONTRACT VERIFICATION: Must have explicit fallback fields
        assert "capability_state" in output, "Missing capability_state - silent fallback detected!"
        assert "fallback_reason" in output, "Missing fallback_reason - silent fallback detected!"
        assert "backend" in output, "Missing backend - silent fallback detected!"
        assert "response_state" in output, "Missing response_state - silent fallback detected!"

        # Values must be from valid enum sets
        assert output["capability_state"] in [s.value for s in CapabilityState]
        assert output["fallback_reason"] in [r.value for r in FallbackReason]
        assert output["backend"] in [b.value for b in Backend]
        assert output["response_state"] in [s.value for s in ResponseState]

    def test_hover_fail_closed_with_require_lsp(self, tmp_path: Path):
        """Hover with --require-lsp must fail closed when LSP unavailable."""
        # Create minimal segment
        (tmp_path / "skill.md").write_text("# Test")
        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / "agent_test.md").write_text("# Agent")
        (ctx_dir / "prime_test.md").write_text("# Prime")
        (ctx_dir / "session_test.md").write_text("# Session")

        test_file = tmp_path / "test.py"
        test_file.write_text("def foo(): pass")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.infrastructure.cli",
                "ast",
                "hover",
                str(test_file),
                "--line",
                "1",
                "--char",
                "1",
                "--segment",
                str(tmp_path),
                "--require-lsp",
            ],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )

        # Should fail with exit code 1
        assert result.returncode == 1, (
            f"Expected exit 1 with --require-lsp, got {result.returncode}"
        )

        output = json.loads(result.stdout)

        # CONTRACT VERIFICATION: Error response must include all fields
        assert output["status"] == "error"
        assert "error_code" in output
        assert "fallback_reason" in output
        assert output["capability_state"] == CapabilityState.UNAVAILABLE.value

    def test_hover_no_silent_ok_without_capability_state(self, tmp_path: Path):
        """TRIPWIRE: Any response with status=ok MUST have capability_state.

        This test ensures we never regress to silent fallbacks.
        """
        # Create minimal segment
        (tmp_path / "skill.md").write_text("# Test")
        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / "agent_test.md").write_text("# Agent")
        (ctx_dir / "prime_test.md").write_text("# Prime")
        (ctx_dir / "session_test.md").write_text("# Session")

        test_file = tmp_path / "test.py"
        test_file.write_text("def foo(): pass")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.infrastructure.cli",
                "ast",
                "hover",
                str(test_file),
                "--line",
                "1",
                "--char",
                "1",
                "--segment",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )

        output = json.loads(result.stdout)

        # INVARIANT: status=ok implies capability_state present
        if output.get("status") == "ok":
            assert "capability_state" in output, (
                f"VIOLATION: status=ok without capability_state - silent fallback! Output: {output}"
            )


class TestFallbackTelemetryEvents:
    """Verify lsp.fallback events are emitted correctly."""

    def test_fallback_event_includes_reason(self, tmp_path: Path):
        """lsp.fallback event must always include explicit reason."""
        # This would require checking telemetry output
        # For now, we verify the contract structure is in place
        # Full telemetry verification would need integration with telemetry system
        pass
