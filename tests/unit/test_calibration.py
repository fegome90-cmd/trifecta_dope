import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import yaml
import os
from src.application.calibration_use_case import AutonomousWeightCalibrationUseCase
from src.domain.result import Ok, Err


class TestAutonomousWeightCalibrationUseCase(unittest.TestCase):
    def setUp(self):
        self.fs = MagicMock()
        self.telemetry = MagicMock()
        self.repo_path = Path("/tmp/test_repo_calib")
        self.repo_path.mkdir(parents=True, exist_ok=True)
        (self.repo_path / "_ctx").mkdir(parents=True, exist_ok=True)
        
        self.aliases_path = self.repo_path / "_ctx" / "aliases.yaml"
        self.aliases_data = {
            "schema_version": 3,
            "features": {
                "test_feature": {"priority": 2, "nl_triggers": ["test query"]}
            }
        }
        with open(self.aliases_path, "w") as f:
            yaml.dump(self.aliases_data, f)
            
        self.prime_path = self.repo_path / "_ctx" / "prime_test.md"
        self.prime_content = """
### index.feature_map
| Feature | Chunk IDs | Paths |
|---------|-----------|-------|
| test_feature | chunk1 | `test.py` |
"""
        self.prime_path.write_text(self.prime_content)
        
        self.dataset_path = self.repo_path / "dataset.md"
        self.dataset_content = '1. "run test" | test_feature'
        self.dataset_path.write_text(self.dataset_content)

        self.calib_uc = AutonomousWeightCalibrationUseCase(self.fs, self.telemetry)

    def tearDown(self):
        import shutil
        if self.repo_path.exists():
            shutil.rmtree(self.repo_path)

    @patch('src.application.calibration_use_case.PlanUseCase')
    def test_execute_boost_priority(self, mock_plan_cls):
        # Mock successful plan
        mock_plan = MagicMock()
        mock_plan_cls.return_value = mock_plan
        mock_plan.execute.return_value = {
            "selected_feature": "test_feature",
            "selected_by": "nl_trigger",
            "paths": ["test.py"]
        }
        
        # We need to re-instantiate or inject the mock
        self.calib_uc.plan_uc = mock_plan
        
        res = self.calib_uc.execute(self.repo_path, self.dataset_path, min_success_rate=0.5)
        print(f"DEBUG: res={res}")
        if res.is_ok():
            print(f"DEBUG: changes={res.unwrap()['changes']}")
        
        self.assertTrue(res.is_ok())
        self.assertEqual(res.unwrap()["status"], "calibrated")
        self.assertIn("Boosted test_feature: 2 -> 3", res.unwrap()["changes"])
        
        # Verify file was updated
        with open(self.aliases_path) as f:
            updated_data = yaml.safe_load(f)
            self.assertEqual(updated_data["features"]["test_feature"]["priority"], 3)

if __name__ == "__main__":
    unittest.main()
