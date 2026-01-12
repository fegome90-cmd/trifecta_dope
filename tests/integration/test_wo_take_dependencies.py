"""
Integration tests for WO take dependency validation.
"""
import tempfile
from pathlib import Path
import yaml


class TestWOTakeDependencies:
    """Test dependency validation in WO take."""

    def test_validate_dependencies_using_domain_unsatisfied(self):
        """Test that validate_dependencies_using_domain returns error for unsatisfied deps."""
        from scripts.ctx_wo_take import validate_dependencies_using_domain

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "_ctx" / "jobs" / "done").mkdir(parents=True)

            # Create a completed WO
            wo_done = {
                "id": "WO-0001",
                "status": "done"
            }
            (repo / "_ctx" / "jobs" / "done" / "WO-0001.yaml").write_text(yaml.safe_dump(wo_done))

            # WO with unsatisfied dependency (include all required fields)
            wo_data = {
                "id": "WO-0002",
                "epic_id": "E-0001",
                "title": "Test WO",
                "priority": "P2",
                "status": "pending",
                "owner": None,
                "dod_id": "DOD-DEFAULT",
                "dependencies": ["WO-0001", "WO-9999"]  # WO-9999 doesn't exist
            }

            is_valid, error = validate_dependencies_using_domain(wo_data, repo)
            assert is_valid is False
            assert "WO-9999" in error

    def test_validate_dependencies_using_domain_all_satisfied(self):
        """Test that validate_dependencies_using_domain passes when all deps satisfied."""
        from scripts.ctx_wo_take import validate_dependencies_using_domain

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "_ctx" / "jobs" / "done").mkdir(parents=True)

            # Create completed WOs
            for wo_id in ["WO-0001", "WO-0002"]:
                wo_done = {"id": wo_id, "status": "done"}
                (repo / "_ctx" / "jobs" / "done" / f"{wo_id}.yaml").write_text(yaml.safe_dump(wo_done))

            # WO with all satisfied dependencies (include all required fields)
            wo_data = {
                "id": "WO-0003",
                "epic_id": "E-0001",
                "title": "Test WO",
                "priority": "P2",
                "status": "pending",
                "owner": None,
                "dod_id": "DOD-DEFAULT",
                "dependencies": ["WO-0001", "WO-0002"]
            }

            is_valid, error = validate_dependencies_using_domain(wo_data, repo)
            assert is_valid is True
            assert error is None

    def test_get_completed_wo_ids(self):
        """Test that get_completed_wo_ids returns correct set."""
        from scripts.ctx_wo_take import get_completed_wo_ids

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "_ctx" / "jobs" / "done").mkdir(parents=True)

            # Create some completed WOs
            for wo_id in ["WO-0001", "WO-0002", "WO-0003"]:
                wo_done = {"id": wo_id, "status": "done"}
                (repo / "_ctx" / "jobs" / "done" / f"{wo_id}.yaml").write_text(yaml.safe_dump(wo_done))

            completed_ids = get_completed_wo_ids(repo)
            assert completed_ids == {"WO-0001", "WO-0002", "WO-0003"}
