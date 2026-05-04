"""
Autonomous Weight Calibration Use Case - Empirical search optimization.

Adjusts the priorities and expansion weights of aliases based on 
empirical performance metrics (PCC).
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.application.plan_use_case import PlanUseCase
from src.application.pcc_metrics import evaluate_pcc, parse_feature_map
from src.domain.result import Ok, Err, Result


class AutonomousWeightCalibrationUseCase:
    """Automatically optimizes search weights in aliases.yaml."""

    def __init__(self, file_system: Any, telemetry: Any = None):
        self.file_system = file_system
        self.telemetry = telemetry
        self.plan_uc = PlanUseCase(file_system, telemetry)

    def execute(
        self, 
        segment_path: Path, 
        dataset_path: Path,
        min_success_rate: float = 0.8,
        boost_step: int = 1
    ) -> Result[Dict[str, Any], str]:
        """
        Run calibration cycle: Evaluate -> Analyze -> Adjust.
        """
        # 1. Load Data
        aliases_path = segment_path / "_ctx" / "aliases.yaml"
        if not aliases_path.exists():
            return Err(f"aliases.yaml not found at {aliases_path}")
            
        try:
            with open(aliases_path) as f:
                aliases_data = yaml.safe_load(f) or {}
        except Exception as e:
            return Err(f"Failed to load aliases: {str(e)}")

        prime_files = list(segment_path.glob("_ctx/prime_*.md"))
        if not prime_files:
            return Err("PRIME file not found for PCC metrics")
        
        try:
            feature_map = parse_feature_map(prime_files[0])
        except Exception as e:
            return Err(f"Failed to parse feature map: {str(e)}")

        # 2. Run Evaluation
        tasks = self._load_tasks(dataset_path)
        if not tasks:
            return Err("No valid tasks found in dataset")

        outcomes: Dict[str, List[bool]] = {} # feature_id -> list of path_correct results
        
        for task, expected_id in tasks:
            plan_res = self.plan_uc.execute(segment_path, task)
            selected_id = plan_res.get("selected_feature")
            selected_by = plan_res.get("selected_by", "fallback")
            
            pcc = evaluate_pcc(
                expected_feature=expected_id,
                predicted_feature=selected_id,
                predicted_paths=plan_res.get("paths", []),
                feature_map=feature_map,
                selected_by=selected_by
            )
            
            if expected_id != "fallback":
                if expected_id not in outcomes:
                    outcomes[expected_id] = []
                outcomes[expected_id].append(pcc["path_correct"])

        # 3. Analyze and Adjust
        changes = []
        features = aliases_data.get("features", {})
        
        for feature_id, results in outcomes.items():
            if not results: continue
            
            success_rate = sum(1 for r in results if r) / len(results)
            current_priority = features.get(feature_id, {}).get("priority", 1)
            
            if success_rate >= min_success_rate and current_priority < 5:
                # Boost high-performing features
                new_priority = min(5, current_priority + boost_step)
                if new_priority != current_priority:
                    features[feature_id]["priority"] = new_priority
                    changes.append(f"Boosted {feature_id}: {current_priority} -> {new_priority}")
            elif success_rate < (min_success_rate / 2) and current_priority > 1:
                # Penalize low-performing features
                new_priority = max(1, current_priority - boost_step)
                if new_priority != current_priority:
                    features[feature_id]["priority"] = new_priority
                    changes.append(f"Reduced {feature_id}: {current_priority} -> {new_priority}")

        # 4. Save Changes
        if changes:
            try:
                aliases_data["features"] = features
                with open(aliases_path, "w") as f:
                    yaml.dump(aliases_data, f, sort_keys=False)
            except Exception as e:
                return Err(f"Failed to save adjusted aliases: {str(e)}")

        return Ok({
            "status": "calibrated" if changes else "no_changes_needed",
            "changes": changes,
            "tasks_evaluated": len(tasks)
        })

    def _load_tasks(self, dataset_path: Path) -> List[tuple[str, str]]:
        """Load tasks and expected feature IDs from markdown dataset."""
        import re
        tasks = []
        if not dataset_path.exists():
            return []
            
        content = dataset_path.read_text()
        for line in content.split("\n"):
            # Format: number. "task" | expected_feature_id
            match = re.match(r'^\d+\.\s+"([^"]+)"\s*\|\s*(\w+)', line)
            if match:
                tasks.append((match.group(1), match.group(2)))
        return tasks
