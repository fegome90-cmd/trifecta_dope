"""Load YAML configs with graceful error handling and auditable markers."""

import sys
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
        Logs warnings to stderr for visibility while maintaining graceful degradation.
        """
        anchors_path = repo_root / "configs" / "anchors.yaml"

        if not anchors_path.exists():
            print(f"[ConfigLoader] anchors.yaml not found at {anchors_path}", file=sys.stderr)
            return {"_missing_config": True, "anchors": {}}

        try:
            with open(anchors_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

                if not isinstance(data, dict) or "anchors" not in data:
                    print(
                        "[ConfigLoader] anchors.yaml invalid structure (missing 'anchors' key)",
                        file=sys.stderr,
                    )
                    return {"_missing_config": True, "anchors": {}}

                return data

        except yaml.YAMLError as e:
            print(f"[ConfigLoader] anchors.yaml YAML parse error: {e}", file=sys.stderr)
            return {"_missing_config": True, "anchors": {}}
        except (IOError, OSError) as e:
            print(f"[ConfigLoader] anchors.yaml read error: {e}", file=sys.stderr)
            return {"_missing_config": True, "anchors": {}}

    @staticmethod
    def load_linter_aliases(repo_root: Path) -> Dict[str, Any]:
        """Load aliases.yaml from repo root configs/.

        Returns:
            - Dict with aliases data if valid
            - {"_missing_config": True, "aliases": []} if missing or invalid

        Graceful degradation: never raises, always returns valid dict.
        Logs warnings to stderr for visibility while maintaining graceful degradation.
        """
        aliases_path = repo_root / "configs" / "aliases.yaml"

        if not aliases_path.exists():
            print(f"[ConfigLoader] aliases.yaml not found at {aliases_path}", file=sys.stderr)
            return {"_missing_config": True, "aliases": []}

        try:
            with open(aliases_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

                if not isinstance(data, dict) or "aliases" not in data:
                    print(
                        "[ConfigLoader] aliases.yaml invalid structure (missing 'aliases' key)",
                        file=sys.stderr,
                    )
                    return {"_missing_config": True, "aliases": []}

                return data

        except yaml.YAMLError as e:
            print(f"[ConfigLoader] aliases.yaml YAML parse error: {e}", file=sys.stderr)
            return {"_missing_config": True, "aliases": []}
        except (IOError, OSError) as e:
            print(f"[ConfigLoader] aliases.yaml read error: {e}", file=sys.stderr)
            return {"_missing_config": True, "aliases": []}
