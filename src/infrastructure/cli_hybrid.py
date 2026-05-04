"""
CLI Hybrid Dispatcher - Routes CLI commands to the running F1 Daemon.

Enables near-zero latency for CLI operations by leveraging the daemon's
shared memory and warm LSP state.
"""

import os
from pathlib import Path
from typing import Any, Dict

from src.domain.result import Ok, Err, Result
from src.infrastructure.daemon_client import get_socket_path, call_daemon


class HybridDispatcher:
    """Client for routing CLI calls to the active Trifecta Daemon."""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.socket_path = get_socket_path(repo_path)

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Result[Any, str]:
        """Call a tool on the running daemon via Unix socket."""
        return call_daemon(self.socket_path, tool_name, arguments)

    def dispatch_search(self, query: str, k: int = 5) -> Result[Any, str]:
        """Route search to daemon or signal fallback."""
        if os.environ.get("TRIFECTA_HYBRID") == "0":
            return Err("Hybrid mode disabled by env")
            
        return self.call_tool("ctx_search", {"query": query, "k": k})

    def dispatch_get(self, ids: list[str], mode: str = "excerpt") -> Result[Any, str]:
        """Route retrieval to daemon or signal fallback."""
        if os.environ.get("TRIFECTA_HYBRID") == "0":
            return Err("Hybrid mode disabled by env")
            
        return self.call_tool("ctx_get", {"ids": ids, "mode": mode})

