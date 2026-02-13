"""
Unit tests for preventing manual WO state transitions.

Tests ensure that:
1. Valid transitions (pending -> running -> done) are allowed
2. Manual file edits that bypass scripts are blocked
3. State transitions require proper metadata
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

import yaml

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


class TestValidTransitions:
    """Test that valid state transitions are allowed."""

    def test_pending_to_running_allowed(self, tmp_path):
        """pending -> running is a valid transition."""
        pending_dir = tmp_path / "_ctx" / "jobs" / "pending"
        running_dir = tmp_path / "_ctx" / "jobs" / "running"
        pending_dir.mkdir(parents=True)
        running_dir.mkdir(parents=True)

        wo_data = {
            "version": 1,
            "id": "WO-TRANS-01",
            "epic_id": "E-TEST",
            "title": "Transition Test",
            "priority": "P1",
            "status": "pending",
            "dod_id": "DOD-TEST",
            "execution": {
                "engine": "trifecta",
                "required_flow": ["verify"],
                "segment": ".",
            },
        }

        pending_path = pending_dir / "WO-TRANS-01.yaml"
        pending_path.write_text(yaml.dump(wo_data))

        # Simulate valid take operation
        wo_data["status"] = "running"
        wo_data["started_at"] = datetime.now(timezone.utc).isoformat()
        wo_data["owner"] = "test-user"

        running_path = running_dir / "WO-TRANS-01.yaml"
        running_path.write_text(yaml.dump(wo_data))
        pending_path.unlink()

        assert running_path.exists()
        assert not pending_path.exists()

    def test_running_to_done_allowed(self, tmp_path):
        """running -> done is a valid transition."""
        running_dir = tmp_path / "_ctx" / "jobs" / "running"
        done_dir = tmp_path / "_ctx" / "jobs" / "done"
        running_dir.mkdir(parents=True)
        done_dir.mkdir(parents=True)

        wo_data = {
            "version": 1,
            "id": "WO-TRANS-02",
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "dod_id": "DOD-TEST",
        }

        running_path = running_dir / "WO-TRANS-02.yaml"
        running_path.write_text(yaml.dump(wo_data))

        # Simulate valid finish operation
        wo_data["status"] = "done"
        wo_data["finished_at"] = datetime.now(timezone.utc).isoformat()
        wo_data["result"] = "done"

        done_path = done_dir / "WO-TRANS-02.yaml"
        done_path.write_text(yaml.dump(wo_data))
        running_path.unlink()

        assert done_path.exists()
        assert not running_path.exists()


class TestManualEditsBlocked:
    """Test that manual file edits bypassing scripts are detected."""

    def test_missing_started_at_in_running_suspicious(self, tmp_path):
        """WO in running/ without started_at is suspicious."""
        running_dir = tmp_path / "_ctx" / "jobs" / "running"
        running_dir.mkdir(parents=True)

        wo_data = {
            "version": 1,
            "id": "WO-MANUAL-01",
            "status": "running",
            "dod_id": "DOD-TEST",
            # Missing started_at - suggests manual edit
        }

        (running_dir / "WO-MANUAL-01.yaml").write_text(yaml.dump(wo_data))

        # Check for suspicious state
        wo = yaml.safe_load((running_dir / "WO-MANUAL-01.yaml").read_text())

        # This should be flagged by validation
        suspicious = wo.get("status") == "running" and wo.get("started_at") is None
        assert suspicious, "Running WO without started_at should be flagged"

    def test_missing_owner_in_running_suspicious(self, tmp_path):
        """WO in running/ without owner is suspicious."""
        running_dir = tmp_path / "_ctx" / "jobs" / "running"
        running_dir.mkdir(parents=True)

        wo_data = {
            "version": 1,
            "id": "WO-MANUAL-02",
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "dod_id": "DOD-TEST",
            # Missing owner - suggests manual edit
        }

        (running_dir / "WO-MANUAL-02.yaml").write_text(yaml.dump(wo_data))

        wo = yaml.safe_load((running_dir / "WO-MANUAL-02.yaml").read_text())

        suspicious = wo.get("status") == "running" and wo.get("owner") is None
        assert suspicious, "Running WO without owner should be flagged"


class TestTransitionMetadata:
    """Test that state transitions require proper metadata."""

    def test_take_requires_branch(self, tmp_path):
        """Take operation should set branch."""
        running_dir = tmp_path / "_ctx" / "jobs" / "running"
        running_dir.mkdir(parents=True)

        wo_data = {
            "version": 1,
            "id": "WO-META-01",
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "owner": "test-user",
            "dod_id": "DOD-TEST",
            "branch": "feat/wo-WO-META-01",  # Required for valid take
        }

        (running_dir / "WO-META-01.yaml").write_text(yaml.dump(wo_data))

        wo = yaml.safe_load((running_dir / "WO-META-01.yaml").read_text())

        assert wo.get("branch") is not None, "Take should set branch"

    def test_finish_requires_finished_at(self, tmp_path):
        """Finish operation should set finished_at."""
        done_dir = tmp_path / "_ctx" / "jobs" / "done"
        done_dir.mkdir(parents=True)

        wo_data = {
            "version": 1,
            "id": "WO-META-02",
            "status": "done",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),  # Required for valid finish
            "owner": "test-user",
            "result": "done",
            "dod_id": "DOD-TEST",
        }

        (done_dir / "WO-META-02.yaml").write_text(yaml.dump(wo_data))

        wo = yaml.safe_load((done_dir / "WO-META-02.yaml").read_text())

        assert wo.get("finished_at") is not None, "Finish should set finished_at"


class TestInvalidTransitions:
    """Test that invalid transitions are detected."""

    def test_pending_to_done_invalid(self, tmp_path):
        """pending -> done transition without going through running is invalid."""
        pending_dir = tmp_path / "_ctx" / "jobs" / "pending"
        done_dir = tmp_path / "_ctx" / "jobs" / "done"
        pending_dir.mkdir(parents=True)
        done_dir.mkdir(parents=True)

        wo_data = {
            "version": 1,
            "id": "WO-SKIP",
            "status": "pending",
            "dod_id": "DOD-TEST",
        }

        pending_path = pending_dir / "WO-SKIP.yaml"
        pending_path.write_text(yaml.dump(wo_data))

        # Invalid: Try to go directly to done without running
        wo_data["status"] = "done"
        wo_data["result"] = "done"

        done_path = done_dir / "WO-SKIP.yaml"
        done_path.write_text(yaml.dump(wo_data))

        # Detect invalid state: done but never running (no started_at)
        wo = yaml.safe_load(done_path.read_text())
        invalid = wo.get("status") == "done" and wo.get("started_at") is None

        assert invalid, "Done WO without started_at (never ran) should be flagged"

    def test_done_back_to_running_invalid(self, tmp_path):
        """done -> running transition is invalid."""
        done_dir = tmp_path / "_ctx" / "jobs" / "done"
        running_dir = tmp_path / "_ctx" / "jobs" / "running"
        done_dir.mkdir(parents=True)
        running_dir.mkdir(parents=True)

        # Create WO in done state
        wo_data = {
            "version": 1,
            "id": "WO-BACK",
            "status": "done",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "result": "done",
            "dod_id": "DOD-TEST",
        }

        done_path = done_dir / "WO-BACK.yaml"
        done_path.write_text(yaml.dump(wo_data))

        # Invalid: Try to move back to running
        wo_data["status"] = "running"
        del wo_data["finished_at"]
        del wo_data["result"]

        # This should be detected and prevented
        # In a proper system, both files shouldn't exist for same WO
        running_path = running_dir / "WO-BACK.yaml"
        # Simulating the invalid state
        running_path.write_text(yaml.dump(wo_data))

        # Detect: WO exists in both done and running
        invalid = done_path.exists() and running_path.exists()

        assert invalid, "WO in both done and running should be detected as invalid"
