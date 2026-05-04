import json
import os
import subprocess
import shutil
from pathlib import Path
import pytest
import time
import select

def run_cmd(cmd: list[str], env: dict = None) -> subprocess.CompletedProcess:
    """Helper to run commands in the isolated environment."""
    return subprocess.run(cmd, capture_output=True, text=True, env=env)

def test_01_environment_isolation(clean_machine):
    """Scenario 1: Verify clean PATH and HOME."""
    fake_home = clean_machine
    assert str(fake_home) in os.environ["HOME"]
    venv_bin = Path(os.environ["PATH"].split(os.pathsep)[0])
    which_res = run_cmd(["which", "trifecta"])
    assert str(venv_bin / "trifecta") in which_res.stdout

def test_02_installation_readiness(clean_machine):
    """Scenario 2 & 3: Verify package installation and version."""
    version_res = run_cmd(["trifecta", "--version"])
    assert version_res.returncode == 0
    assert "0.2.0-rc1" in version_res.stdout

def test_04_doctor_readiness(clean_machine):
    """Scenario 4: Verify trifecta doctor works in clean repo."""
    repo = clean_machine / "demo_doctor"
    repo.mkdir()
    run_cmd(["trifecta", "create", "--segment", str(repo)])
    (repo / "docs").mkdir()
    (repo / "docs" / "intro.md").write_text("Context.")
    run_cmd(["trifecta", "ctx", "build", "--segment", str(repo)])
    
    doctor_res = run_cmd(["trifecta", "doctor", "--repo", str(repo)])
    assert doctor_res.returncode == 0
    assert "Health Score: 100/100" in doctor_res.stdout

def test_05_bootstrap_dry_run(clean_machine):
    """Scenario 5: Verify bootstrap dry-run doesn't write."""
    fake_home = clean_machine
    opencode_dir = fake_home / ".config" / "opencode"
    opencode_dir.mkdir(parents=True)
    settings_path = opencode_dir / "settings.json"
    settings_path.write_text(json.dumps({"mcpServers": {}}))
    
    bootstrap_res = run_cmd(["trifecta", "bootstrap", "--agent", "opencode", "--dry-run"])
    assert "dry_run=True" in bootstrap_res.stdout
    assert json.loads(settings_path.read_text()) == {"mcpServers": {}}

def test_06_bootstrap_apply_and_idempotency(clean_machine):
    """Scenario 6 & 7: Verify bootstrap apply and idempotency."""
    fake_home = clean_machine
    opencode_dir = fake_home / ".config" / "opencode"
    if not opencode_dir.exists(): opencode_dir.mkdir(parents=True)
    settings_path = opencode_dir / "settings.json"
    settings_path.write_text(json.dumps({"mcpServers": {}}))
    
    run_cmd(["trifecta", "bootstrap", "--agent", "opencode"])
    config = json.loads(settings_path.read_text())
    assert "trifecta" in config["mcpServers"]
    
    run_cmd(["trifecta", "bootstrap", "--agent", "opencode"])
    config_2 = json.loads(settings_path.read_text())
    assert len(config_2["mcpServers"]) == 1

def test_09_mcp_startup_and_silent_sync(clean_machine):
    """Scenario 9 & 10: Verify MCP startup triggers silent sync."""
    fake_home = clean_machine
    test_repo = fake_home / "demo_mcp"
    if test_repo.exists(): shutil.rmtree(test_repo)
    test_repo.mkdir()
    (test_repo / "README.md").write_text("# Demo Repo")
    # Pre-scaffold to ensure success
    run_cmd(["trifecta", "create", "--segment", str(test_repo)])
    
    venv_bin = Path(os.environ["PATH"].split(os.pathsep)[0])
    mcp_bin = venv_bin / "trifecta-mcp"
    cmd = [str(mcp_bin)] if mcp_bin.exists() else ["python", "-m", "src.interfaces.mcp.server"]
    
    process = subprocess.Popen(
        cmd + ["--repo", str(test_repo), "--mode", "auto"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        init_req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        process.stdin.write(init_req + "\n")
        process.stdin.flush()
        process.stdout.readline()
        
        # Poll for READY
        ready_found = False
        for i in range(10):
            time.sleep(1)
            health_req = json.dumps({"jsonrpc": "2.0", "id": 200 + i, "method": "tools/call", "params": {"name": "ctx_health"}})
            process.stdin.write(health_req + "\n")
            process.stdin.flush()
            
            line = process.stdout.readline()
            if "READY" in line:
                ready_found = True
                break
        
        assert ready_found
        assert (test_repo / "_ctx" / "context_pack.json").exists()
    finally:
        process.terminate()

def test_12_mcp_timeout_management(clean_machine):
    """Scenario 12: Verify MCP build timeout results in error."""
    fake_home = clean_machine
    test_repo = fake_home / "demo_timeout"
    if test_repo.exists(): shutil.rmtree(test_repo)
    test_repo.mkdir()
    (test_repo / "README.md").write_text("# Timeout Test")
    run_cmd(["trifecta", "create", "--segment", str(test_repo)])

    venv_bin = Path(os.environ["PATH"].split(os.pathsep)[0])
    mcp_bin = venv_bin / "trifecta-mcp"
    cmd = [str(mcp_bin)] if mcp_bin.exists() else ["python", "-m", "src.interfaces.mcp.server"]

    # Use artificial delay in the environment
    env = {**os.environ, "TRIFECTA_SYNC_DELAY": "5"}
    
    process = subprocess.Popen(
        cmd + ["--repo", str(test_repo), "--timeout", "1"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env
    )
    
    try:
        init_req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        process.stdin.write(init_req + "\n")
        process.stdin.flush()
        process.stdout.readline()
        
        # Call search immediately (it will trigger SYNCING)
        search_req = json.dumps({
            "jsonrpc": "2.0", "id": 3, 
            "method": "tools/call", 
            "params": {"name": "ctx_search", "arguments": {"query": "test"}}
        })
        process.stdin.write(search_req + "\n")
        process.stdin.flush()
        process.stdout.readline() # Read SYNCING error
        
        # Wait for timeout to hit
        time.sleep(2)
        
        # Call again, should be FAILED due to timeout
        process.stdin.write(search_req + "\n")
        process.stdin.flush()
        
        stdout = process.stdout.readline()
        assert "LSP_TIMEOUT" in stdout or "FAILED" in stdout
    finally:
        process.terminate()
