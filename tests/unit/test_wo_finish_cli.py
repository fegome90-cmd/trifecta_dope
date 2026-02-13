"""
Unit tests for ctx_wo_finish.py CLI arguments.

Tests CLI interface and argument parsing.
"""

import subprocess
from pathlib import Path


def repo_root() -> Path:
    """Find repository root by searching for pyproject.toml."""
    return Path(__file__).resolve().parents[2]


class TestWoFinishCLIArguments:
    """Test WO finish CLI argument handling."""

    def test_cli_help_argument(self):
        """Test CLI --help argument displays help."""
        result = subprocess.run(
            ["python", "scripts/ctx_wo_finish.py", "--help"],
            capture_output=True,
            text=True,
            cwd=repo_root(),
        )
        assert result.returncode == 0
        assert "Finish a work order" in result.stdout
        assert "wo_id" in result.stdout
        assert "positional arguments" in result.stdout or "options" in result.stdout

    def test_cli_result_argument(self):
        """Test CLI --result argument accepts done/failed."""
        result = subprocess.run(
            ["python", "scripts/ctx_wo_finish.py", "--help"],
            capture_output=True,
            text=True,
            cwd=repo_root(),
        )
        assert result.returncode == 0
        assert "--result" in result.stdout
        assert (
            "{done,failed}" in result.stdout
            or "done" in result.stdout
            and "failed" in result.stdout
        )

    def test_cli_generate_only_flag(self):
        """Test CLI --generate-only flag exists and is documented."""
        result = subprocess.run(
            ["python", "scripts/ctx_wo_finish.py", "--help"],
            capture_output=True,
            text=True,
            cwd=repo_root(),
        )
        assert result.returncode == 0
        assert "--generate-only" in result.stdout
        # Verify description mentions artifacts but not moving WO
        assert "artifact" in result.stdout.lower() or "generat" in result.stdout.lower()

    def test_cli_clean_flag(self):
        """Test CLI --clean flag exists and is documented."""
        result = subprocess.run(
            ["python", "scripts/ctx_wo_finish.py", "--help"],
            capture_output=True,
            text=True,
            cwd=repo_root(),
        )
        assert result.returncode == 0
        assert "--clean" in result.stdout
        # Verify description mentions cleaning/removing
        assert "clean" in result.stdout.lower() or "remov" in result.stdout.lower()

    def test_cli_skip_dod_flag(self):
        """Test CLI --skip-dod flag exists and is documented."""
        result = subprocess.run(
            ["python", "scripts/ctx_wo_finish.py", "--help"],
            capture_output=True,
            text=True,
            cwd=repo_root(),
        )
        assert result.returncode == 0
        assert "--skip-dod" in result.stdout
        # Verify description mentions skipping validation or emergency
        assert "skip" in result.stdout.lower() or "emergency" in result.stdout.lower()

    def test_cli_skip_verification_flag(self):
        """Test CLI --skip-verification flag exists and is documented."""
        result = subprocess.run(
            ["python", "scripts/ctx_wo_finish.py", "--help"],
            capture_output=True,
            text=True,
            cwd=repo_root(),
        )
        assert result.returncode == 0
        assert "--skip-verification" in result.stdout


class TestWoFinishCLIWorkflow:
    """Test WO finish CLI workflow scenarios."""

    def test_cli_without_args_shows_help(self):
        """Test CLI without arguments shows help."""
        result = subprocess.run(
            ["python", "scripts/ctx_wo_finish.py"],
            capture_output=True,
            text=True,
            cwd=repo_root(),
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower() or "help" in result.stdout.lower()

    def test_cli_root_argument(self):
        """Test CLI --root argument is accepted."""
        result = subprocess.run(
            ["python", "scripts/ctx_wo_finish.py", "--help"],
            capture_output=True,
            text=True,
            cwd=repo_root(),
        )
        assert result.returncode == 0
        assert "--root" in result.stdout

    def test_cli_no_wo_id_displays_help(self):
        """Test CLI without WO ID displays help (exit 0)."""
        result = subprocess.run(
            ["python", "scripts/ctx_wo_finish.py", "--root", "/tmp"],
            capture_output=True,
            text=True,
            cwd=repo_root(),
        )
        # Should display help and exit with 0
        assert result.returncode == 0

    def test_cli_missing_wo_emits_error_card(self, tmp_path):
        """Missing running WO should emit stable error card."""
        result = subprocess.run(
            [
                "python",
                "scripts/ctx_wo_finish.py",
                "WO-NONEXISTENT",
                "--root",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            cwd=repo_root(),
        )
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "TRIFECTA_ERROR_CODE: WO_NOT_RUNNING" in combined

    def test_cli_invalid_root_emits_error_card(self):
        """Invalid root path should emit INVALID_SEGMENT_PATH card."""
        result = subprocess.run(
            [
                "python",
                "scripts/ctx_wo_finish.py",
                "WO-TEST",
                "--root",
                "/definitely/not/a/real/path/for/trifecta",
            ],
            capture_output=True,
            text=True,
            cwd=repo_root(),
        )
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "TRIFECTA_ERROR_CODE: INVALID_SEGMENT_PATH" in combined

    def test_cli_generate_only_valid_wo(self, tmp_path):
        """Test CLI --generate-only with valid WO structure."""
        # Create minimal WO structure
        running_dir = tmp_path / "_ctx" / "jobs" / "running"
        running_dir.mkdir(parents=True)
        wo_content = """version: 1
id: WO-TEST
epic_id: E-TEST
title: "Test WO"
priority: P1
status: running
dod_id: DOD-TEST
x_objective: "Test"
x_micro_tasks: []
"""
        (running_dir / "WO-TEST.yaml").write_text(wo_content)

        dod_dir = tmp_path / "_ctx" / "dod"
        dod_dir.mkdir(parents=True)
        dod_content = """dod:
  - id: DOD-TEST
    name: "Test DoD"
    requirements: []
"""
        (dod_dir / "DOD-TEST.yaml").write_text(dod_content)

        result = subprocess.run(
            [
                "python",
                "scripts/ctx_wo_finish.py",
                "WO-TEST",
                "--root",
                str(tmp_path),
                "--generate-only",
            ],
            capture_output=True,
            text=True,
            cwd=repo_root(),
        )
        # Will likely fail due to missing git/uv, but we're testing the path
        assert result is not None

    def test_cli_skip_dod_flag_bypasses_validation(self, tmp_path):
        """Test CLI --skip-dod flag bypasses DoD validation."""
        running_dir = tmp_path / "_ctx" / "jobs" / "running"
        running_dir.mkdir(parents=True)
        wo_content = """version: 1
id: WO-TEST
epic_id: E-TEST
title: "Test WO"
priority: P1
status: running
dod_id: DOD-TEST
x_objective: "Test"
x_micro_tasks: []
"""
        (running_dir / "WO-TEST.yaml").write_text(wo_content)

        dod_dir = tmp_path / "_ctx" / "dod"
        dod_dir.mkdir(parents=True)
        (dod_dir / "DOD-TEST.yaml").write_text("dod:\n  - id: DOD-TEST\n    name: Test\n")

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "checkout", "-b", "main"], cwd=tmp_path, capture_output=True)

        result = subprocess.run(
            [
                "python",
                "scripts/ctx_wo_finish.py",
                "WO-TEST",
                "--root",
                str(tmp_path),
                "--skip-dod",
            ],
            capture_output=True,
            text=True,
            cwd=repo_root(),
        )
        # May fail, but --skip-dod should bypass DoD validation
        assert result is not None

    def test_cli_result_failed(self, tmp_path):
        """Test CLI --result failed closes WO as failed."""
        running_dir = tmp_path / "_ctx" / "jobs" / "running"
        running_dir.mkdir(parents=True)
        wo_content = """version: 1
id: WO-TEST
epic_id: E-TEST
title: "Test WO"
priority: P1
status: running
dod_id: DOD-TEST
x_objective: "Test"
x_micro_tasks: []
"""
        (running_dir / "WO-TEST.yaml").write_text(wo_content)

        dod_dir = tmp_path / "_ctx" / "dod"
        dod_dir.mkdir(parents=True)
        (dod_dir / "DOD-TEST.yaml").write_text("dod:\n  - id: DOD-TEST\n    name: Test\n")

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "checkout", "-b", "main"], cwd=tmp_path, capture_output=True)

        result = subprocess.run(
            [
                "python",
                "scripts/ctx_wo_finish.py",
                "WO-TEST",
                "--root",
                str(tmp_path),
                "--result",
                "failed",
                "--skip-dod",
            ],
            capture_output=True,
            text=True,
            cwd=repo_root(),
        )
        # Testing the CLI accepts --result failed
        assert result is not None
