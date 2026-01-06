"""
CLI Black-Box Acceptance Tests - Real World Scenarios

Tests Trifecta CLI como lo usaría un agente, sin mocks ni introspección.
Solo subprocess + assertions sobre exit codes y output.

Refactored to be fail-closed with proper segment initialization.
"""

import subprocess
from pathlib import Path
import pytest

TRIFECTA_ROOT = Path(__file__).resolve().parents[2]


def run_trifecta(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Execute trifecta CLI and capture output."""
    return subprocess.run(
        ["uv", "--directory", str(TRIFECTA_ROOT), "run", "trifecta", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def assert_no_crashes(result: subprocess.CompletedProcess[str]) -> None:
    """Assert no Python exceptions or tracebacks in output."""
    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    assert "Traceback" not in combined, f"Found traceback in output:\n{combined}"
    assert "Exception:" not in combined, f"Found exception in output:\n{combined}"


def setup_trifecta_segment(path: Path) -> None:
    """Initialize a minimal Trifecta segment with create + sync.

    Fail-closed: asserts on errors instead of skipping.
    """
    # Create skill.md (required by trifecta)
    (path / "skill.md").write_text("""---
name: test_segment
description: Test segment
---
# Test
""")

    result = run_trifecta("create", "-s", str(path), cwd=path)
    assert result.returncode == 0, f"trifecta create failed:\n{result.stderr}"


# =========================
# A) Segmentos / Roots
# =========================


def test_sync_in_real_repo(tmp_path: Path):
    """Scenario: -s . dentro de repo real (típico)."""
    # Fixture mínimo
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\nversion='0.0.1'\n")
    setup_trifecta_segment(tmp_path)

    result = run_trifecta("ctx", "sync", "-s", str(tmp_path), cwd=tmp_path)

    assert result.returncode == 0, f"Sync failed:\n{result.stdout}\n{result.stderr}"
    assert_no_crashes(result)
    assert "Build complete" in result.stdout or "Validation Passed" in result.stdout


def test_sync_without_git_or_pyproject(tmp_path: Path):
    """Scenario: repo sin .git ni pyproject.toml → debe fail-closed con mensaje claro."""
    # Empty directory - no setup
    result = run_trifecta("ctx", "sync", "-s", str(tmp_path), cwd=tmp_path)

    # Debe fallar de forma controlada
    assert result.returncode != 0, "Should fail on invalid segment"
    assert_no_crashes(result)

    combined = result.stdout + result.stderr
    # Mensaje claro (sin stacktrace)
    assert any(
        indicator in combined.lower()
        for indicator in ["not found", "invalid", "missing", "required", "error"]
    ), f"Expected clear error message, got:\n{combined}"


def test_path_with_spaces_and_unicode(tmp_path: Path):
    """Scenario: path con espacios y unicode."""
    # Create dir with spaces and unicode
    weird_path = tmp_path / "Proyecto Ñandú"
    weird_path.mkdir()
    (weird_path / "pyproject.toml").write_text("[project]\nname='test'\nversion='0.0.1'\n")
    setup_trifecta_segment(weird_path)

    result = run_trifecta("ctx", "sync", "-s", str(weird_path), cwd=weird_path)

    assert result.returncode == 0, f"Should handle unicode paths:\n{result.stderr}"
    assert_no_crashes(result)


# =========================
# B) Concurrencia / Locks / Daemon
# =========================


def test_sync_three_times_sequential(tmp_path: Path):
    """Scenario: ctx sync 3 veces seguidas (start/stop)."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\nversion='0.0.1'\n")
    setup_trifecta_segment(tmp_path)

    for i in range(3):
        result = run_trifecta("ctx", "sync", "-s", str(tmp_path), cwd=tmp_path)
        assert result.returncode == 0, f"Run {i + 1} failed:\n{result.stderr}"
        assert_no_crashes(result)


@pytest.mark.slow  # Marked slow instead of skip - requires manual testing
def test_sync_parallel(tmp_path: Path):
    """Scenario: ctx sync en paralelo → debe fail-closed con mensaje claro.

    This test is marked slow because parallel execution is hard to test deterministically.
    The assertion verifies that concurrent access doesn't cause Python crashes.
    """
    import concurrent.futures

    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\nversion='0.0.1'\n")
    setup_trifecta_segment(tmp_path)

    def run_sync():
        return run_trifecta("ctx", "sync", "-s", str(tmp_path), cwd=tmp_path)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run_sync) for _ in range(2)]
        results = [f.result() for f in futures]

    # At least one should succeed, neither should crash
    for result in results:
        assert_no_crashes(result)

    success_count = sum(1 for r in results if r.returncode == 0)
    assert success_count >= 1, "At least one parallel sync should succeed"


# =========================
# C) Entradas Reales de Agentes
# =========================


def test_search_with_realistic_query(tmp_path: Path):
    """Scenario: agente busca 'README.md' o concepto común."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\nversion='0.0.1'\n")
    (tmp_path / "README.md").write_text("# Test Project\n\nA test readme.")
    setup_trifecta_segment(tmp_path)

    # Sync first
    sync = run_trifecta("ctx", "sync", "-s", str(tmp_path), cwd=tmp_path)
    assert sync.returncode == 0, f"Sync failed:\n{sync.stderr}"

    # Search
    result = run_trifecta("ctx", "search", "-s", str(tmp_path), "-q", "README", cwd=tmp_path)

    # May return 0 (found) or 0 (not found with message)
    # Important: no crashes
    assert_no_crashes(result)


def test_agent_relative_path_from_wrong_cwd(tmp_path: Path):
    """Scenario: agente usa ruta relativa desde cwd incorrecto."""
    repo = tmp_path / "my_project"
    repo.mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname='test'\nversion='0.0.1'\n")

    # Agente corre desde tmp_path, no desde repo
    # Usa -s con ruta relativa (mal)
    result = run_trifecta("ctx", "sync", "-s", "my_project", cwd=tmp_path)

    # Puede funcionar (si resuelve relativa) o fallar
    # Importante: sin crashes y mensaje claro si falla
    assert_no_crashes(result)

    if result.returncode != 0:
        combined = result.stdout + result.stderr
        assert any(
            hint in combined.lower()
            for hint in ["not found", "invalid", "path", "directory", "error"]
        ), f"Expected clear path error, got:\n{combined}"


# =========================
# Real Agent Failure Example
# =========================


def test_agent_common_mistake_missing_segment_flag():
    """Scenario: agente olvida -s flag (común)."""
    # This will use current directory as segment (may or may not work)
    # Important: should not crash with confusing message
    result = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync"],
        capture_output=True,
        text=True,
        cwd="/tmp",  # Neutral location
    )

    # May succeed if /tmp is valid segment, or fail
    assert_no_crashes(result)

    # If fails, should have helpful message
    if result.returncode != 0:
        combined = result.stdout + result.stderr
        # Should NOT be cryptic internal error
        assert (
            "segment" in combined.lower()
            or "directory" in combined.lower()
            or "option" in combined.lower()
        )
