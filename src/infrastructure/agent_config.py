import json
import os
import shutil
from pathlib import Path
from typing import Dict, Optional, Protocol
from src.domain.result import Result, Ok, Err

class AgentConfigAdapter(Protocol):
    """Protocol for AI agent configuration management."""
    def detect(self) -> bool: ...
    def read(self) -> Result[Dict, str]: ...
    def write(self, config: Dict) -> Result[bool, str]: ...
    def inject_mcp(self, mcp_id: str, mcp_config: Dict) -> Result[bool, str]: ...

class BaseJSONConfigAdapter:
    """Base class for agents using JSON-based settings."""

    def __init__(self, config_path: Path):
        self.config_path = config_path.resolve()
        self.backup_path = self.config_path.with_suffix(".json.bak")

    def detect(self) -> bool:
        return self.config_path.exists()

    def read(self) -> Result[Dict, str]:
        if not self.config_path.exists():
            return Err(f"Config file not found: {self.config_path}")
        try:
            with open(self.config_path, "r") as f:
                return Ok(json.load(f))
        except Exception as e:
            return Err(f"Failed to read JSON config: {e}")

    def _atomic_write(self, data: Dict) -> Result[bool, str]:
        """Write JSON atomically with validation and backup."""
        tmp_path = self.config_path.with_suffix(".json.tmp")
        try:
            # 1. Validate data
            json_str = json.dumps(data, indent=2)
            
            # 2. Create backup
            if self.config_path.exists():
                shutil.copy2(self.config_path, self.backup_path)
            
            # 3. Write to temp file
            with open(tmp_path, "w") as f:
                f.write(json_str)
            
            # 4. Atomic rename
            os.replace(tmp_path, self.config_path)
            return Ok(True)
        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink()
            return Err(f"Atomic write failed: {e}")

    def rollback(self) -> Result[bool, str]:
        """Restore from backup."""
        if not self.backup_path.exists():
            return Err("No backup found for rollback")
        try:
            os.replace(self.backup_path, self.config_path)
            return Ok(True)
        except Exception as e:
            return Err(f"Rollback failed: {e}")

class ClaudeConfigAdapter(BaseJSONConfigAdapter):
    """Adapter for Claude Code (separate MCP files strategy)."""

    def __init__(self, mcp_dir: Path):
        # Claude uses one JSON per server in ~/.claude/mcp/
        self.mcp_dir = mcp_dir.resolve()
        super().__init__(self.mcp_dir / "trifecta.json")

    def detect(self) -> bool:
        return self.mcp_dir.is_dir()

    def inject_mcp(self, mcp_id: str, mcp_config: Dict) -> Result[bool, str]:
        """Claude uses separate files, so we just write trifecta.json."""
        if not self.mcp_dir.exists():
            return Err(f"Claude MCP directory not found: {self.mcp_dir}")
        return self._atomic_write(mcp_config)

class OpenCodeConfigAdapter(BaseJSONConfigAdapter):
    """Adapter for OpenCode (merged settings.json strategy)."""

    def inject_mcp(self, mcp_id: str, mcp_config: Dict) -> Result[bool, str]:
        """OpenCode merges into settings.json."""
        res = self.read()
        if isinstance(res, Err):
            return res
        
        data = res.value
        if "mcpServers" not in data:
            data["mcpServers"] = {}
        
        # Idempotency check
        if mcp_id in data["mcpServers"] and data["mcpServers"][mcp_id] == mcp_config:
            return Ok(True) # No change needed
            
        data["mcpServers"][mcp_id] = mcp_config
        return self._atomic_write(data)
