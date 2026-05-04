from pathlib import Path
from typing import List, Optional
from src.domain.result import Result, Ok, Err
from src.infrastructure.agent_config import ClaudeConfigAdapter, OpenCodeConfigAdapter
from src.application.discovery_service import EngramDiscoveryService

class BootstrapUseCase:
    """Agnostic bootstrap orchestrator for Trifecta ecosystem."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root.resolve()
        self.discovery = EngramDiscoveryService()

    def execute(self, agents: List[str], dry_run: bool = False) -> Result[dict, str]:
        results = {
            "installed_bin": False,
            "agent_configs": [],
            "engram": self.discovery.discover()
        }

        # 1. Detect agents and inject MCP
        mcp_config = {
            "command": "uvx",
            "args": [
                "--from", 
                "git+https://github.com/Gentleman-Programming/trifecta_dope", 
                "trifecta-mcp", 
                "run", 
                "--repo", 
                str(self.repo_root)
            ],
            "env": {
                "TRIFECTA_DOPE_DIR": str(self.repo_root)
            }
        }

        for agent in agents:
            adapter = self._get_adapter(agent)
            if not adapter or not adapter.detect():
                continue
            
            if dry_run:
                results["agent_configs"].append({"agent": agent, "status": "dry-run", "path": str(adapter.config_path)})
                continue

            inject_res = adapter.inject_mcp("trifecta", mcp_config)
            if isinstance(inject_res, Ok):
                results["agent_configs"].append({"agent": agent, "status": "success", "path": str(adapter.config_path)})
            else:
                results["agent_configs"].append({"agent": agent, "status": "error", "message": inject_res.error})

        return Ok(results)

    def _get_adapter(self, agent: str):
        home = Path.home()
        if agent == "claude":
            return ClaudeConfigAdapter(home / ".claude" / "mcp")
        if agent == "opencode":
            return OpenCodeConfigAdapter(home / ".config" / "opencode" / "settings.json")
        return None
