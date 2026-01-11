import pytest
import subprocess
import json
import os
import shutil

# Use a test-specific env to enable persistence
ENV_WITH_PERSIST = os.environ.copy()
ENV_WITH_PERSIST["TRIFECTA_AST_PERSIST"] = "1"


@pytest.fixture
def fresh_cli_workspace(tmp_path):
    """
    Creates a temporary workspace with:
    - A python file to parse
    - A .trifecta directory for cache
    """
    ws = tmp_path / "ws"
    ws.mkdir()

    # Create target file
    target = ws / "target.py"
    target.write_text("def foo():\n    pass\n")

    # Create segment metadata (to satisfy validator if needed, though AST CLI might be loose)
    (ws / ".trifecta").mkdir()

    return ws


def run_ast_symbols(cwd, uri, telemetry_file):
    """Helper to run CLI command"""
    cmd = [
        "uv",
        "run",
        "trifecta",
        "ast",
        "symbols",
        uri,
        "--segment",
        ".",
        "--telemetry",
        "lite",  # Force telemetry to capture cache status
    ]

    # We need to ensure telemetry writes to a known location or query the default one
    # The default telemetry path is usually cwd/_ctx/telemetry/events.jsonl
    # But we can't easily override it via args in 'lite' mode without --telemetry-dir env maybe?
    # Let's rely on standard Output JSON for cache_status/cache_key first,
    # and Telemetry file second if needed.
    # The CLI output JSON *does* contain "cache_status": result.status

    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=ENV_WITH_PERSIST)
    return result


def test_ast_persistence_cross_run(fresh_cli_workspace):
    """
    Verifies that running the AST command twice with persistence enabled
    results in a Cache Hit on the second run.
    """
    cwd = fresh_cli_workspace
    uri = "sym://python/mod/target"  # defaults to target.py in cwd

    # Run 1: Cold
    # Ensure cache is clean
    cache_dir = cwd / ".trifecta" / "cache"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)

    res1 = run_ast_symbols(cwd, uri, None)
    assert res1.returncode == 0, f"Run 1 failed: {res1.stderr}"

    data1 = json.loads(res1.stdout)
    assert data1["status"] == "ok"
    # Depending on implementation details, first run might be "miss" or "generated"
    # The SkeletonMapBuilder returns status in result
    status1 = data1.get("cache_status")
    assert status1 in ("miss", "generated"), f"Expected cold run, got {status1}"

    # Check if DB was created
    db_files = list(cache_dir.glob("*.db"))
    assert len(db_files) > 0, "SQLite DB not created after Run 1"

    # Run 2: Warm
    res2 = run_ast_symbols(cwd, uri, None)
    assert res2.returncode == 0, f"Run 2 failed: {res2.stderr}"

    data2 = json.loads(res2.stdout)
    status2 = data2.get("cache_status")

    # Assert Cross-Run Persistence
    assert status2 == "hit", f"Expected cache hit on second run, got {status2}"
    assert data2["symbols"] == data1["symbols"]
    assert data2["cache_key"] == data1["cache_key"]


def test_ast_persistence_env_var_control(fresh_cli_workspace):
    """
    Verifies that we can toggle persistence off via env var (simulated by not setting it)
    """
    cwd = fresh_cli_workspace
    uri = "sym://python/mod/target"

    # environment WITHOUT the persist flag
    env_no_persist = os.environ.copy()
    if "TRIFECTA_AST_PERSIST" in env_no_persist:
        del env_no_persist["TRIFECTA_AST_PERSIST"]

    cmd = [
        "uv",
        "run",
        "trifecta",
        "ast",
        "symbols",
        uri,
        "--segment",
        ".",
    ]

    # Run 1
    subprocess.run(cmd, cwd=cwd, env=env_no_persist, capture_output=True)

    # Check NO DB created
    cache_dir = cwd / ".trifecta" / "cache"
    if cache_dir.exists():
        db_files = list(cache_dir.glob("*.db"))
        assert len(db_files) == 0, f"Expected no DB with persistence off, found {db_files}"
