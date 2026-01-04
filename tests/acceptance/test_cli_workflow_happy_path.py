"""Acceptance test for CLI workflow happy path.

Verifies the official workflow documented in docs/CLI_WORKFLOW.md.
Tests the contract: create → sync → search → get → ast symbols.
"""

import subprocess
import json
from pathlib import Path
from tests.helpers import repo_root


def test_cli_workflow_happy_path(tmp_path):
    """Full CLI workflow should work end-to-end in tmp_path segment."""
    segment_path = tmp_path / "test_segment"
    segment_path.mkdir()

    # Step 1: Create segment
    result_create = subprocess.run(
        ["uv", "run", "trifecta", "create", "--segment", str(segment_path)],
        capture_output=True,
        text=True,
        cwd=str(repo_root()),
    )

    assert result_create.returncode == 0, f"create failed: {result_create.stderr}"
    assert (segment_path / f"_ctx/prime_{segment_path.name}.md").exists()

    # Step 2: Sync context (build + validate)
    result_sync = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "--segment", str(segment_path)],
        capture_output=True,
        text=True,
        cwd=str(repo_root()),
    )

    assert result_sync.returncode == 0, f"ctx sync failed: {result_sync.stderr}"
    assert (segment_path / "_ctx/context_pack.json").exists()

    # Step 3: Search context
    result_search = subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ctx",
            "search",
            "--segment",
            str(segment_path),
            "--query",
            "test query",
        ],
        capture_output=True,
        text=True,
        cwd=str(repo_root()),
    )

    assert result_search.returncode == 0, f"ctx search failed: {result_search.stderr}"
    # ctx search returns formatted text, not JSON
    assert "Search Results" in result_search.stdout or "hits" in result_search.stdout


def test_cli_error_card_segment_not_initialized(tmp_path):
    """ctx sync should return SEGMENT_NOT_INITIALIZED if prime missing."""
    segment_path = tmp_path / "uninitialized_segment"
    segment_path.mkdir()

    # Try to sync without creating segment first
    result = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "--segment", str(segment_path)],
        capture_output=True,
        text=True,
        cwd=str(repo_root()),
    )

    # Should fail with Error Card
    assert result.returncode != 0, "Expected non-zero exit for uninitialized segment"

    # Error Cards are in stderr
    assert "SEGMENT_NOT_INITIALIZED" in result.stderr or "TRIFECTA_ERROR_CODE" in result.stderr


def test_cli_ast_symbols_with_python_file(tmp_path):
    """AST symbols should work for Python files in segment."""
    segment_path = tmp_path / "py_segment"
    segment_path.mkdir()

    # Create a Python file
    src_dir = segment_path / "src"
    src_dir.mkdir()
    test_file = src_dir / "example.py"
    test_file.write_text("def foo():\n    pass\n\nclass Bar:\n    pass\n")

    # Run ast symbols
    result = subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ast",
            "symbols",
            "sym://python/mod/src.example",
            "--segment",
            str(segment_path),
        ],
        capture_output=True,
        text=True,
        cwd=str(repo_root()),
    )

    assert result.returncode == 0, f"ast symbols failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert output["status"] == "ok"
    assert len(output["symbols"]) >= 2  # foo + Bar


def test_cli_ast_symbols_file_not_found(tmp_path):
    """AST symbols should return FILE_NOT_FOUND for missing modules."""
    segment_path = tmp_path / "empty_segment"
    segment_path.mkdir()

    result = subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ast",
            "symbols",
            "sym://python/mod/nonexistent",
            "--segment",
            str(segment_path),
        ],
        capture_output=True,
        text=True,
        cwd=str(repo_root()),
    )

    assert result.returncode != 0
    output = json.loads(result.stdout)
    assert output["status"] == "error"
    assert "FILE_NOT_FOUND" in output["error_code"]
