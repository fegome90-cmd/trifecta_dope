import os
import shutil
from pathlib import Path
from src.infrastructure.telemetry import Telemetry


def test_telemetry_no_telemetry_kill_switch(tmp_path):
    """CONTRACT: TRIFECTA_NO_TELEMETRY=1 must be an absolute NO-OP."""
    segment_root = tmp_path / "segment"
    segment_root.mkdir()
    # Create marker to prevent resolve_segment_root from falling back to CWD (repo root)
    (segment_root / "pyproject.toml").write_text("[project]\nname='test'\n")

    # Set kill switch
    os.environ["TRIFECTA_NO_TELEMETRY"] = "1"
    try:
        telemetry = Telemetry(root=segment_root)

        # 1. Directory should NOT be created
        telemetry_dir = segment_root / "_ctx" / "telemetry"
        assert not telemetry_dir.exists()

        # 2. Writes should NOT happen even if called
        telemetry.event("test_cmd", {"arg": 1}, {"res": "ok"}, 10)
        telemetry.flush()

        assert not telemetry_dir.exists()
    finally:
        del os.environ["TRIFECTA_NO_TELEMETRY"]


def test_telemetry_dir_override_redirection(tmp_path):
    """CONTRACT: TRIFECTA_TELEMETRY_DIR must redirect all writes away from repo."""
    segment_root = tmp_path / "segment"
    segment_root.mkdir()
    # Create marker
    (segment_root / "pyproject.toml").write_text("[project]\nname='test'\n")

    external_dir = tmp_path / "external_telemetry"
    os.environ["TRIFECTA_TELEMETRY_DIR"] = str(external_dir)

    try:
        telemetry = Telemetry(root=segment_root)

        # 1. External directory should be created
        assert external_dir.exists()

        # 2. Repo directory should NOT be created
        repo_telemetry_dir = segment_root / "_ctx" / "telemetry"
        assert not repo_telemetry_dir.exists()

        # 3. Writes should go to external dir
        telemetry.event("test_cmd", {"arg": 1}, {"res": "ok"}, 10)
        telemetry.flush()

        assert (external_dir / "events.jsonl").exists()
        assert (external_dir / "last_run.json").exists()
    finally:
        del os.environ["TRIFECTA_TELEMETRY_DIR"]


def test_telemetry_precedence_no_telemetry_wins(tmp_path):
    """CONTRACT: TRIFECTA_NO_TELEMETRY > TRIFECTA_TELEMETRY_DIR."""
    segment_root = tmp_path / "segment"
    segment_root.mkdir()
    # Create marker
    (segment_root / "pyproject.toml").write_text("[project]\nname='test'\n")

    external_dir = tmp_path / "external_telemetry"

    os.environ["TRIFECTA_NO_TELEMETRY"] = "1"
    os.environ["TRIFECTA_TELEMETRY_DIR"] = str(external_dir)

    try:
        telemetry = Telemetry(root=segment_root)

        # 1. NO-OP should win: no dirs created
        assert not external_dir.exists()
        assert not (segment_root / "_ctx" / "telemetry").exists()

        telemetry.event("test_cmd", {"arg": 1}, {"res": "ok"}, 10)
        assert not external_dir.exists()
    finally:
        del os.environ["TRIFECTA_NO_TELEMETRY"]
        del os.environ["TRIFECTA_TELEMETRY_DIR"]


def test_telemetry_dir_no_contamination_on_flush(tmp_path):
    """TRIPWIRE: Ensure flush does not accidentally create repo dirs when overridden."""
    segment_base = tmp_path / "repo"
    segment_base.mkdir()
    # Create marker
    (segment_base / "pyproject.toml").write_text("[project]\nname='test'\n")

    override_dir = tmp_path / "override"
    os.environ["TRIFECTA_TELEMETRY_DIR"] = str(override_dir)

    try:
        t = Telemetry(root=segment_base)
        t.event("test", {}, {}, 1)
        t.flush()

        # Check contamination
        repo_ctx = segment_base / "_ctx"
        assert not repo_ctx.exists(), "Telemetry flush contaminated repo root!"
    finally:
        del os.environ["TRIFECTA_TELEMETRY_DIR"]
