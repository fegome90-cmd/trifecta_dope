"""Load YAML configs with graceful error handling and auditable markers."""

from pathlib import Path
from typing import Dict, Any
import yaml


class ConfigLoader:
    """Load YAML configs from repo root configs/ directory.

    Returns auditable markers when configs are missing or invalid.
    """

    @staticmethod
    def load_anchors(repo_root: Path) -> Dict[str, Any]:
        """Load anchors.yaml from repo root configs/.

        Returns:
            - Dict with anchors data if valid
            - {"_missing_config": True, "anchors": {}} if missing or invalid

        Graceful degradation: never raises, always returns valid dict.
        """
        anchors_path = repo_root / "configs" / "anchors.yaml"

        if not anchors_path.exists():
            return {"_missing_config": True, "anchors": {}}

        try:
            with open(anchors_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

                if not isinstance(data, dict) or "anchors" not in data:
                    return {"_missing_config": True, "anchors": {}}

                return data

        except (yaml.YAMLError, IOError, OSError):
            return {"_missing_config": True, "anchors": {}}

    @staticmethod
    def load_linter_aliases(repo_root: Path) -> Dict[str, Any]:
        """Load aliases.yaml from repo root configs/.

        Returns:
            - Dict with aliases data if valid
            - {"_missing_config": True, "aliases": []} if missing or invalid

        Graceful degradation: never raises, always returns valid dict.
        """
        aliases_path = repo_root / "configs" / "aliases.yaml"

        if not aliases_path.exists():
            return {"_missing_config": True, "aliases": []}

        try:
            with open(aliases_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

                if not isinstance(data, dict) or "aliases" not in data:
                    return {"_missing_config": True, "aliases": []}

                return data

        except (yaml.YAMLError, IOError, OSError):
            return {"_missing_config": True, "aliases": []}
