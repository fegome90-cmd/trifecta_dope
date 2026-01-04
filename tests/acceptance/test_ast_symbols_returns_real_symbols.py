"""Acceptance tests for ast symbols CLI command (M1).

Tests are deterministic and use tmp_path only (no repo state dependency).
"""

import subprocess
import json
from pathlib import Path


def test_ast_symbols_cli_returns_real_symbols(tmp_path):
    """CLI should return real symbols from Python file."""
    # Create segment structure
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    test_file = src_dir / "example.py"
    test_file.write_text("def foo():\n    pass\n\nclass Bar:\n    pass\n")

    # Run CLI
    result = subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ast",
            "symbols",
            "sym://python/mod/src.example",
            "--segment",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        cwd="/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope",
    )

    # Verify return code
    assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"

    # Parse JSON output
    output = json.loads(result.stdout)

    # Verify contract
    assert output["status"] == "ok", f"Expected status=ok, got: {output}"
    assert "segment_root" in output
    assert "file_rel" in output
    assert "symbols" in output

    # Verify symbols content
    assert len(output["symbols"]) >= 2, f"Expected >=2 symbols, got: {len(output['symbols'])}"

    names = [s["name"] for s in output["symbols"]]
    assert "foo" in names, f"Expected 'foo' in symbols, got: {names}"
    assert "Bar" in names, f"Expected 'Bar' in symbols, got: {names}"

    # Verify structure of each symbol
    for sym in output["symbols"]:
        assert "kind" in sym
        assert "name" in sym
        assert "line" in sym
        assert sym["kind"] in ["function", "class"]


def test_ast_symbols_cli_file_not_found(tmp_path):
    """CLI should return error JSON for missing module (fail-closed)."""
    # Run CLI with nonexistent module
    result = subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ast",
            "symbols",
            "sym://python/mod/nonexistent",
            "--segment",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        cwd="/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope",
    )

    # Verify exit code (should be non-zero)
    assert result.returncode != 0, "Expected non-zero exit code for missing file"

    # Parse JSON output
    output = json.loads(result.stdout)

    # Verify error structure
    assert output["status"] == "error"
    assert "error_code" in output
    assert "FILE_NOT_FOUND" in output["error_code"]
    assert "message" in output


def test_ast_symbols_cli_empty_file(tmp_path):
    """CLI should return empty symbols list for file with no defs/classes."""
    # Create file with only comments
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    test_file = src_dir / "empty.py"
    test_file.write_text("# Just a comment\npass\n")

    # Run CLI
    result = subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ast",
            "symbols",
            "sym://python/mod/src.empty",
            "--segment",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        cwd="/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope",
    )

    # Verify
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "ok"
    assert output["symbols"] == [], "Expected empty symbols list"
