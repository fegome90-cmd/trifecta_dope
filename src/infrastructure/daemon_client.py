"""
Shared client logic for connecting to the Trifecta F1 Daemon via Unix Socket.
Uses ONLY standard library and src.domain.result to ensure <15ms startup time.
"""

import json
import socket
import time
import hashlib
from pathlib import Path
from typing import Any, Dict

from src.domain.result import Ok, Err, Result

def get_socket_path(repo_path: Path) -> Path:
    """Generate the deterministic socket path for a given repository."""
    repo_hash = hashlib.sha256(str(repo_path.resolve()).encode()).hexdigest()[:12]
    return Path(f"/tmp/trifecta_f1_{repo_hash}.sock")

def call_daemon(socket_path: Path, tool_name: str, arguments: Dict[str, Any]) -> Result[Any, str]:
    """Call a tool on the running daemon via Unix socket."""
    if not socket_path.exists():
        return Err(f"Daemon not reachable via socket: {socket_path}")

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect(str(socket_path))
            
            # Standard MCP-like JSON-RPC frame over socket
            request = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            s.sendall(json.dumps(request).encode() + b"\n")
            
            # Read response (simple line-based for v1)
            data = b""
            while True:
                chunk = s.recv(4096)
                if not chunk: break
                data += chunk
                if b"\n" in data: break
            
            response = json.loads(data.decode())
            
            if "error" in response:
                return Err(response["error"].get("message", "Unknown daemon error"))
            
            result = response.get("result", {})
            # Content is usually a list with type: text for MCP tools
            if "content" in result and isinstance(result["content"], list):
                text = result["content"][0].get("text", "")
                try:
                    return Ok(json.loads(text))
                except json.JSONDecodeError:
                    return Ok(text)
            
            return Ok(result)

    except Exception as e:
        return Err(f"Hybrid dispatch failed: {str(e)}")
