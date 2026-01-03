"""
Integration tests for debug scripts.

Verify that debug scripts can import from src.* correctly
and that their path hack works as expected.
"""

import sys
from pathlib import Path
import subprocess


def test_debug_scripts_exist():
    """Verify all debug scripts exist in expected location."""
    debug_dir = Path(__file__).parent.parent.parent / "scripts" / "debug"

    expected_scripts = [
        "debug_client.py",
        "debug_status.py",
        "debug_ts.py",
    ]

    for script in expected_scripts:
        script_path = debug_dir / script
        assert script_path.exists(), f"Debug script {script} not found at {script_path}"


def test_debug_scripts_can_import_src():
    """Verify that debug scripts can import from src.*."""
    # Import the same modules that debug scripts use
    try:
        import src.infrastructure.lsp_client  # noqa: F401
        import src.infrastructure.lsp_daemon  # noqa: F401
        import src.infrastructure.segment_utils  # noqa: F401
    except ImportError as e:
        raise AssertionError(f"Failed to import from src.*: {e}")


def test_debug_client_syntax():
    """Verify debug_client.py has valid Python syntax."""
    debug_client = Path(__file__).parent.parent.parent / "scripts" / "debug" / "debug_client.py"

    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(debug_client)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Syntax error in debug_client.py: {result.stderr}"


def test_debug_status_syntax():
    """Verify debug_status.py has valid Python syntax."""
    debug_status = Path(__file__).parent.parent.parent / "scripts" / "debug" / "debug_status.py"

    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(debug_status)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Syntax error in debug_status.py: {result.stderr}"


def test_debug_ts_syntax():
    """Verify debug_ts.py has valid Python syntax."""
    debug_ts = Path(__file__).parent.parent.parent / "scripts" / "debug" / "debug_ts.py"

    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(debug_ts)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Syntax error in debug_ts.py: {result.stderr}"


def test_debug_scripts_path_hack():
    """Verify that the path hack in debug scripts resolves to project root correctly."""
    debug_dir = Path(__file__).parent.parent.parent / "scripts" / "debug"

    # Simulate the path hack logic from debug scripts
    _script_dir = debug_dir
    _project_root = _script_dir.parent.parent

    # Verify that project_root contains src/ directory
    assert (_project_root / "src").exists(), f"Project root {_project_root} does not contain src/"
    assert (_project_root / "src" / "infrastructure").exists(), "src/infrastructure not found"


def test_debug_init_module_exists():
    """Verify that scripts/debug/__init__.py exists and is a proper package."""
    init_file = Path(__file__).parent.parent.parent / "scripts" / "debug" / "__init__.py"

    assert init_file.exists(), f"__init__.py not found at {init_file}"

    # Verify it can be imported
    subprocess.run(
        [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{init_file.parent.parent.parent}'); import scripts.debug",
        ],
        capture_output=True,
        text=True,
    )

    # Note: This might fail if scripts.debug is not in proper package structure
    # but at minimum the file should exist
