import subprocess
import json
import pytest
from pathlib import Path
import time
import sys

def test_daemon_client_parity():
    """Verify that trifecta-fast.py and uv run trifecta ctx return identical payload shapes and error handling."""
    
    repo_path = Path(".").resolve()
    
    # 1. Search Query
    query = "SkeletonMapBuilder"
    
    # Run heavy CLI
    res_cli = subprocess.run(["uv", "run", "trifecta", "ctx", "oracle", "--segment", ".", "--query", query], capture_output=True, text=True)
    assert res_cli.returncode == 0
    cli_out = json.loads(res_cli.stdout)
    
    # Run fast proxy
    res_fast = subprocess.run([sys.executable, "scripts/trifecta-fast.py", "oracle", "--segment", ".", "--query", query], capture_output=True, text=True)
    assert res_fast.returncode == 0
    fast_out = json.loads(res_fast.stdout)
    
    # Shape checks
    assert "fidelity" in cli_out and "fidelity" in fast_out
    assert cli_out["fidelity"] == fast_out["fidelity"]
    assert "prime_chunks" in cli_out and "prime_chunks" in fast_out
    assert len(cli_out["prime_chunks"]) == len(fast_out["prime_chunks"])
    
    # Error checking
    res_fast_err = subprocess.run([sys.executable, "scripts/trifecta-fast.py", "search", "--segment", "."], capture_output=True, text=True)
    assert res_fast_err.returncode != 0
    assert "Error: --query is required for search" in res_fast_err.stderr
