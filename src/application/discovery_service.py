import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class EngramDiscoveryResult:
    detected: bool
    configured: bool
    reachable: bool
    method: Optional[str] = None
    path: Optional[str] = None
    version: Optional[str] = None

class EngramDiscoveryService:
    """Discovery service for Engram following layered detection contract."""

    def __init__(self, explicit_path: Optional[str] = None):
        self.explicit_path = explicit_path

    def discover(self) -> EngramDiscoveryResult:
        # Layer 1: Explicit
        if self.explicit_path:
            path = Path(self.explicit_path)
            if path.exists():
                return EngramDiscoveryResult(
                    detected=True, configured=True, reachable=True, 
                    method="explicit", path=str(path)
                )

        # Layer 2: Environment
        env_home = os.environ.get("ENGRAM_HOME")
        if env_home:
            path = Path(env_home)
            if path.exists():
                return EngramDiscoveryResult(
                    detected=True, configured=True, reachable=True, 
                    method="env_var", path=str(path)
                )

        # Layer 3: Runtime (PATH)
        engram_bin = shutil.which("engram")
        if engram_bin:
            return EngramDiscoveryResult(
                detected=True, configured=True, reachable=True, 
                method="runtime", path=engram_bin
            )

        # Layer 4: Filesystem (Default)
        std_path = Path.home() / ".engram"
        if std_path.exists():
            return EngramDiscoveryResult(
                detected=True, configured=True, reachable=True, 
                method="filesystem", path=str(std_path)
            )

        return EngramDiscoveryResult(detected=False, configured=False, reachable=False)
