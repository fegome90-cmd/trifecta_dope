"""Regression test: DaemonRunner must pass repo_root (not runtime_dir) to LSPClient.

This test verifies the fix for the bug where DaemonRunner._initialize_lsp_client()
was passing self.runtime_dir instead of self.repo_root to LSPClient, causing
LSP to fail with "relative path can't be expressed as a file URI".

See: docs/daemon-lsp-scope/daemon_lsp_operationalization_plan_v2.md
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.infrastructure.daemon.runner import DaemonRunner


def test_daemon_runner_uses_repo_root_for_lsp_client(tmp_path: Path) -> None:
    """Verify DaemonRunner passes repo_root (not runtime_dir) to LSPClient."""
    runtime_dir = tmp_path / "runtime"
    repo_root = tmp_path / "repo"
    runtime_dir.mkdir()
    repo_root.mkdir()

    runner = DaemonRunner(runtime_dir=runtime_dir, repo_root=repo_root)

    with patch("src.infrastructure.daemon.runner.LSPClient") as mock_lsp_cls:
        mock_lsp = MagicMock()
        mock_lsp_cls.return_value = mock_lsp

        runner._initialize_lsp_client()

        # Verify LSPClient was called with repo_root, not runtime_dir
        mock_lsp_cls.assert_called_once_with(repo_root, telemetry=None)
        mock_lsp.start.assert_called_once()


def test_daemon_runner_from_env_reads_repo_root(tmp_path: Path) -> None:
    """Verify DaemonRunner.from_env() reads TRIFECTA_REPO_ROOT from environment."""
    runtime_dir = tmp_path / "runtime"
    repo_root = tmp_path / "repo"
    runtime_dir.mkdir()
    repo_root.mkdir()

    env = {
        "TRIFECTA_RUNTIME_DIR": str(runtime_dir),
        "TRIFECTA_REPO_ROOT": str(repo_root),
    }

    with patch.dict(os.environ, env, clear=False):
        with patch("src.infrastructure.daemon.runner.is_runtime_dir_allowed", return_value=True):
            runner = DaemonRunner.from_env()

    assert runner.runtime_dir == runtime_dir.resolve()
    assert runner.repo_root == repo_root.resolve()


def test_daemon_runner_from_env_fails_without_repo_root(tmp_path: Path) -> None:
    """Verify DaemonRunner.from_env() fails if TRIFECTA_REPO_ROOT is missing."""
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()

    env = {
        "TRIFECTA_RUNTIME_DIR": str(runtime_dir),
    }
    # Remove TRIFECTA_REPO_ROOT if present
    env_clean = {k: v for k, v in os.environ.items() if k != "TRIFECTA_REPO_ROOT"}
    env_clean.update(env)

    with patch.dict(os.environ, env_clean, clear=True):
        with patch("src.infrastructure.daemon.runner.is_runtime_dir_allowed", return_value=True):
            try:
                DaemonRunner.from_env()
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "TRIFECTA_REPO_ROOT" in str(e)
