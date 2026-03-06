"""
Infrastructure layer: File system operations for skills.

Discovers SKILL.md files and extracts frontmatter YAML.
Does NOT validate - that's in the domain layer.

Author: Trifecta Team
Date: 2026-03-05
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # PyYAML already in deps (pyproject.toml)

from src.domain.skill_contracts import SkillMeta, SkillInput


@dataclass(frozen=True)
class DiscoveredSkill:
    """A skill discovered from the filesystem."""

    path: Path
    meta: SkillMeta
    content: str  # Full SKILL.md content (for display)


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Full file content with optional frontmatter

    Returns:
        (frontmatter_dict, body_content)
        If no frontmatter, returns ({}, content)

    Note: YAML errors are silently caught and return empty frontmatter.
    This matches the codebase pattern of graceful degradation.
    """
    lines = content.strip().split("\n")

    if not lines or lines[0].strip() != "---":
        return {}, content

    # Find closing ---
    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return {}, content

    frontmatter_text = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1 :])

    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError:
        frontmatter = {}

    return frontmatter, body


def dict_to_skill_meta(data: dict[str, Any], source_path: str = "") -> SkillMeta:
    """
    Convert frontmatter dict to SkillMeta.

    This is the bridge between YAML and domain model.
    Handles missing/optional fields gracefully.
    """
    name = data.get("name", "")
    description = data.get("description", "")

    # Parse requires
    requires_raw = data.get("requires", [])
    requires = [str(r) for r in requires_raw] if isinstance(requires_raw, list) else []

    # Parse outputs
    outputs_raw = data.get("outputs", [])
    outputs = [str(o) for o in outputs_raw] if isinstance(outputs_raw, list) else []

    # Parse levels
    levels_raw = data.get("levels", [])
    levels = [str(level) for level in levels_raw] if isinstance(levels_raw, list) else []

    # Parse inputs (more complex)
    inputs: list[SkillInput] = []
    inputs_raw = data.get("inputs", [])
    if isinstance(inputs_raw, list):
        for inp_data in inputs_raw:
            if isinstance(inp_data, dict):
                inputs.append(
                    SkillInput(
                        name=str(inp_data.get("name", "")),
                        type=str(inp_data.get("type", "string")),
                        required=bool(inp_data.get("required", True)),
                        description=str(inp_data.get("description", "")),
                    )
                )

    return SkillMeta(
        name=name,
        description=description,
        requires=requires,
        inputs=inputs,
        outputs=outputs,
        levels=levels,
        source_path=source_path,
    )


def discover_skills(skills_dir: Path) -> list[DiscoveredSkill]:
    """
    Discover all SKILL.md files in a directory.

    Args:
        skills_dir: Root directory to search (e.g., skills/)

    Returns:
        List of DiscoveredSkill objects
    """
    if not skills_dir.exists():
        return []

    skills: list[DiscoveredSkill] = []

    # Find all SKILL.md files recursively
    for skill_file in skills_dir.rglob("SKILL.md"):
        try:
            content = skill_file.read_text()
            frontmatter, _ = parse_frontmatter(content)
            meta = dict_to_skill_meta(frontmatter, str(skill_file))
            skills.append(
                DiscoveredSkill(
                    path=skill_file,
                    meta=meta,
                    content=content,
                )
            )
        except Exception:
            # Skip files that can't be read/parsed
            continue

    return skills


def discover_skills_from_paths(paths: list[Path]) -> list[DiscoveredSkill]:
    """
    Discover skills from specific paths.

    Args:
        paths: List of directories or specific SKILL.md files

    Returns:
        List of DiscoveredSkill objects
    """
    skills: list[DiscoveredSkill] = []

    for path in paths:
        if path.is_file() and path.name == "SKILL.md":
            try:
                content = path.read_text()
                frontmatter, _ = parse_frontmatter(content)
                meta = dict_to_skill_meta(frontmatter, str(path))
                skills.append(DiscoveredSkill(path=path, meta=meta, content=content))
            except Exception:
                # Silently skip files that can't be read (permission, encoding, etc.)
                # Matches codebase pattern - see cli.py:200, cli.py:209 for similar patterns
                continue
        elif path.is_dir():
            skills.extend(discover_skills(path))

    return skills
