"""Filesystem operations for alias YAML files.

This module provides:
- Loading aliases from YAML files (schema_version 1)
- Saving generated aliases to YAML files
- Merging manual and generated aliases with precedence

Design principles:
- Manual aliases always take precedence over generated
- Generated aliases only fill gaps (aliases not in manual)
- Fail-safe loading (errors return empty dict)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


# Expected schema version for alias files
EXPECTED_SCHEMA_VERSION = 1

# Default filenames
MANUAL_ALIASES_FILENAME = "aliases.yaml"
GENERATED_ALIASES_FILENAME = "aliases.generated.yaml"


def load_aliases_yaml(file_path: Path) -> dict[str, list[str]]:
    """Load aliases from a YAML file.

    Args:
        file_path: Path to the YAML file.

    Returns:
        Dict mapping alias keys to lists of skill names.
        Empty dict if file doesn't exist or is invalid.
    """
    if not file_path.exists():
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data: object = yaml.safe_load(f)

        if not isinstance(data, dict):
            return {}

        # Validate schema version
        schema_version = data.get("schema_version")
        if schema_version != EXPECTED_SCHEMA_VERSION:
            return {}

        # Extract aliases
        aliases = data.get("aliases", {})
        if not isinstance(aliases, dict):
            return {}

        # Normalize keys to lowercase
        result: dict[str, list[str]] = {}
        for key, skills in aliases.items():
            if isinstance(key, str) and isinstance(skills, list):
                # Validate all skills are strings
                valid_skills = [s for s in skills if isinstance(s, str)]
                if valid_skills:
                    result[key.lower()] = valid_skills

        return result

    except (yaml.YAMLError, OSError, ValueError) as e:
        logger.debug(f"Failed to load aliases from {file_path}: {e}")
        return {}


def merge_aliases(
    manual: dict[str, list[str]], generated: dict[str, list[str]]
) -> dict[str, list[str]]:
    """Merge manual and generated aliases.

    Precedence rules:
    - Manual aliases always win on conflicts
    - Generated aliases only add keys not in manual

    Args:
        manual: Manual aliases (higher precedence).
        generated: Generated aliases (lower precedence).

    Returns:
        Merged aliases dict.
    """
    result: dict[str, list[str]] = {}

    # Add manual aliases first (highest precedence)
    for key, skills in manual.items():
        result[key] = list(skills)  # Copy to avoid mutation

    # Add generated aliases only if not in manual
    for key, skills in generated.items():
        if key not in result:
            result[key] = list(skills)  # Copy to avoid mutation

    return result


def save_generated_aliases(output_path: Path, aliases: dict[str, list[str]]) -> None:
    """Save generated aliases to YAML file.

    Creates parent directories if needed.
    Writes with schema_version: 1.

    Args:
        output_path: Path to write the file.
        aliases: Dict of aliases to save.
    """
    # Create parent directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build output structure
    data = {"schema_version": EXPECTED_SCHEMA_VERSION, "aliases": aliases}

    # Write YAML
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=True, allow_unicode=True)


# AliasMerger and GeneratedAliasWriter classes kept for backward compatibility
# These simple wrappers delegate to the module-level functions above.


class AliasMerger:
    """Merge manual and generated aliases for a segment.

    Thin wrapper around merge_aliases() for backward compatibility.

    Reads from:
    - _ctx/aliases.yaml (manual)
    - _ctx/aliases.generated.yaml (generated)
    """

    def __init__(self, segment_path: Path) -> None:
        """Initialize the merger.

        Args:
            segment_path: Path to the segment root directory.
        """
        self.segment_path = segment_path
        self.ctx_path = segment_path / "_ctx"

    def load_manual(self) -> dict[str, list[str]]:
        """Load manual aliases from _ctx/aliases.yaml."""
        return load_aliases_yaml(self.ctx_path / MANUAL_ALIASES_FILENAME)

    def load_generated(self) -> dict[str, list[str]]:
        """Load generated aliases from _ctx/aliases.generated.yaml."""
        return load_aliases_yaml(self.ctx_path / GENERATED_ALIASES_FILENAME)

    def merge(self) -> dict[str, list[str]]:
        """Merge manual and generated aliases."""
        return merge_aliases(self.load_manual(), self.load_generated())


class GeneratedAliasWriter:
    """Write generated aliases to YAML file.

    Thin wrapper around save_generated_aliases() for backward compatibility.
    """

    def __init__(
        self,
        segment_path: Path,
        output_path: Path | None = None,
        dry_run: bool = False,
    ) -> None:
        """Initialize the writer.

        Args:
            segment_path: Path to the segment root directory.
            output_path: Custom output path (optional).
            dry_run: If True, don't write the file.
        """
        self.segment_path = segment_path
        self.ctx_path = segment_path / "_ctx"
        self.output_path = output_path or (self.ctx_path / GENERATED_ALIASES_FILENAME)
        self.dry_run = dry_run

    def write(self, aliases: dict[str, list[str]]) -> Path:
        """Write aliases to the output file.

        Args:
            aliases: Dict of aliases to write.

        Returns:
            Path to the output file (even in dry-run mode).
        """
        if not self.dry_run:
            save_generated_aliases(self.output_path, aliases)
        return self.output_path


def load_skills_manifest(segment_path: Path) -> list[dict[str, str]]:
    """Load skills from skills_manifest.json.

    Args:
        segment_path: Path to the segment root.

    Returns:
        List of canonical skill dicts with name, source_path, description.
        Empty list if manifest doesn't exist.

    Raises:
        ValueError: If the on-disk manifest exists but is not canonical schema v2.
    """
    manifest_path = segment_path / "_ctx" / "skills_manifest.json"

    if not manifest_path.exists():
        return []

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data: object = json.load(f)
    except (json.JSONDecodeError, OSError, ValueError) as e:
        raise ValueError(f"skills_manifest.json violates canonical manifest contract: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(
            "skills_manifest.json violates canonical manifest contract: "
            "manifest must be a JSON object"
        )

    schema_version = data.get("schema_version")
    if schema_version != 2:
        raise ValueError(
            "skills_manifest.json violates canonical manifest contract: "
            "schema_version=2 is required for alias consumers"
        )

    skills = data.get("skills", [])
    if not isinstance(skills, list):
        raise ValueError(
            "skills_manifest.json violates canonical manifest contract: 'skills' must be a list"
        )

    result: list[dict[str, str]] = []
    required_fields = ("id", "name", "relative_path", "description", "source", "canonical")
    for idx, raw_skill in enumerate(skills):
        if not isinstance(raw_skill, dict):
            raise ValueError(
                "skills_manifest.json violates canonical manifest contract: "
                f"entry {idx} must be an object"
            )

        missing = [field for field in required_fields if field not in raw_skill]
        if missing:
            raise ValueError(
                "skills_manifest.json violates canonical manifest contract: "
                f"entry {idx} missing required fields: {', '.join(missing)}"
            )

        canonical_flag = raw_skill["canonical"]
        if not isinstance(canonical_flag, bool):
            raise ValueError(
                "skills_manifest.json violates canonical manifest contract: "
                f"entry {idx} 'canonical' must be boolean"
            )
        if not canonical_flag:
            continue

        # Validate name is not null/None before str() conversion
        if raw_skill["name"] is None:
            raise ValueError(
                "skills_manifest.json violates canonical manifest contract: "
                f"entry {idx} 'name' must not be null"
            )
        name = str(raw_skill["name"]).strip()
        if raw_skill.get("relative_path") is None:
            raise ValueError(
                "skills_manifest.json violates canonical manifest contract: "
                f"entry {idx} 'relative_path' must not be null"
            )
        relative_path = str(raw_skill["relative_path"]).strip()
        description = str(raw_skill.get("description") or "").strip()
        if not name or not relative_path:
            raise ValueError(
                "skills_manifest.json violates canonical manifest contract: "
                f"entry {idx} requires non-empty name and relative_path"
            )

        result.append(
            {
                "name": name,
                # Compatibility key expected by KeywordExtractor.
                "source_path": relative_path,
                "description": description,
            }
        )

    return result
