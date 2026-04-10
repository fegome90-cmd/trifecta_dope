"""Skill manifest domain model for skill_hub indexing.

Schema v2 contract:
- id: stable skill identifier (e.g., "skill:my-skill")
- name: human-readable name
- relative_path: path relative to segment root
- description: description for search
- source: source collection

Fail-closed: Invalid entries cause Err, not silent skip.

Author: Trifecta Team
Date: 2026-03-19
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from src.domain.result import Err, Ok, Result

logger = logging.getLogger(__name__)

# Required fields for schema v2
REQUIRED_FIELDS = ("id", "name", "relative_path", "description", "source")


@dataclass(frozen=True)
class SkillManifestEntry:
    """A single skill entry in the manifest."""

    id: str
    name: str
    relative_path: str
    description: str
    source: str
    canonical: bool = True
    tags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def skill_id(self) -> str:
        """
        Stable identity of this skill.
        Does not change between builds.
        Format: skill:{name}
        """
        return self.id

    @property
    def chunk_id(self) -> str:
        """
        Chunk identifier including content hash.
        CHANGES when content changes.
        Format: skill:{name}:{content_hash}
        """
        # Use name (not skill_id which includes skill: prefix)
        return f"skill:{self.name}:{self._content_hash}"

    _content_hash: str = field(default="", repr=False)

    @classmethod
    def from_dict(
        cls, data: dict[str, object], content_hash: str = ""
    ) -> "SkillManifestEntry":
        """Create entry from dictionary."""
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            relative_path=str(data.get("relative_path", "")),
            description=str(data.get("description", "")),
            source=str(data.get("source", "")),
            canonical=bool(data.get("canonical", True)),
            tags=tuple(data.get("tags", []) or []),  # type: ignore
            _content_hash=content_hash,
        )


@dataclass(frozen=True)
class SkillManifest:
    """
    Manifest of discoverable skills for a skill_hub segment.

    Schema v2: Only entries in this manifest are discoverable.
    Fail-closed: Invalid manifest causes Err, not degradation.
    """

    schema_version: int
    skills: tuple[SkillManifestEntry, ...]

    def find_by_relative_path(self, relative_path: str) -> SkillManifestEntry | None:
        """Find a skill by its relative path."""
        for skill in self.skills:
            if skill.relative_path == relative_path:
                return skill
        return None

    def find_by_name(self, name: str) -> SkillManifestEntry | None:
        """Find a skill by its name."""
        for skill in self.skills:
            if skill.name == name:
                return skill
        return None

    @classmethod
    def load(
        cls, manifest_path: Path, segment_path: Path
    ) -> Result["SkillManifest", list[str]]:
        """
        Load and validate manifest from disk.

        Args:
            manifest_path: Path to skills_manifest.json
            segment_path: Path to segment root (for file validation)

        Returns:
            Ok(SkillManifest) if valid
            Err(list[str]) with error messages if invalid

        Fail-closed: Any validation error returns Err.
        """
        errors: list[str] = []

        # 1. Check file exists
        if not manifest_path.exists():
            return Err([f"Manifest not found: {manifest_path}"])

        # 2. Parse JSON
        try:
            raw_content = manifest_path.read_text(encoding="utf-8")
            data = json.loads(raw_content)
        except json.JSONDecodeError as e:
            return Err([f"Failed to parse manifest JSON: {e}"])
        except OSError as e:
            return Err([f"Failed to read manifest: {e}"])

        if not isinstance(data, dict):
            return Err([f"Manifest must be a JSON object, got {type(data).__name__}"])

        # 3. Detect schema version
        schema_version = data.get("schema_version", 1)

        # 4. Migrate if needed
        if schema_version == 1:
            migration_result = cls._migrate_v1_to_v2(data, segment_path)
            if isinstance(migration_result, Err):
                return migration_result
            data = migration_result.value
            schema_version = 2

        # 5. Validate and build entries
        skills_data = data.get("skills", [])
        if not isinstance(skills_data, list):
            return Err([f"'skills' must be a list, got {type(skills_data).__name__}"])

        valid_entries: list[SkillManifestEntry] = []

        for i, skill_data in enumerate(skills_data):
            if not isinstance(skill_data, dict):
                errors.append(f"Entry {i}: must be an object, got {type(skill_data).__name__}")
                continue

            # Validate required fields
            for field_name in REQUIRED_FIELDS:
                if field_name not in skill_data or not skill_data[field_name]:
                    errors.append(
                        f"Entry {i}: missing required field '{field_name}'"
                    )

            if errors:
                continue  # Skip further validation for this entry

            # Validate file exists
            relative_path = str(skill_data.get("relative_path", ""))
            file_path = segment_path / relative_path
            if not file_path.exists():
                errors.append(
                    f"Entry {i} '{skill_data.get('name', '?')}': "
                    f"file not found: {relative_path}"
                )
                continue

            # Compute content hash
            content_hash = cls._compute_content_hash(file_path)

            # Build entry
            entry = SkillManifestEntry.from_dict(skill_data, content_hash)
            valid_entries.append(entry)

        if errors:
            return Err(errors)

        return Ok(
            cls(
                schema_version=schema_version,
                skills=tuple(valid_entries),
            )
        )

    @classmethod
    def admit_and_persist(
        cls,
        manifest_path: Path,
        segment_path: Path,
        declared_policy: str,
    ) -> Result["SkillManifest", list[str]]:
        """Admission boundary for skill_hub manifests (normalize -> validate -> persist)."""
        admitted = cls.admit(
            manifest_path,
            segment_path,
            declared_policy=declared_policy,
        )
        if isinstance(admitted, Err):
            return admitted

        manifest, canonical_doc = admitted.value
        try:
            manifest_path.write_text(
                json.dumps(canonical_doc, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except OSError as e:
            return Err([f"[Provenance] Failed to persist canonical manifest: {e}"])

        return Ok(manifest)

    @classmethod
    def admit(
        cls,
        manifest_path: Path,
        segment_path: Path,
        declared_policy: str,
    ) -> Result[tuple["SkillManifest", dict[str, object]], list[str]]:
        """Admission boundary for skill_hub manifests (normalize + validate, no persistence)."""
        errors: list[str] = []

        if declared_policy != "skill_hub":
            return Err([
                "[Policy consistency] Admission requires declared policy 'skill_hub'"
            ])

        if not manifest_path.exists():
            return Err([f"[Shape] Manifest not found: {manifest_path}"])

        try:
            raw_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return Err([f"[Shape] Failed to parse manifest JSON: {e}"])
        except OSError as e:
            return Err([f"[Shape] Failed to read manifest: {e}"])

        if not isinstance(raw_data, dict):
            return Err([f"[Shape] Manifest must be a JSON object, got {type(raw_data).__name__}"])

        input_schema = raw_data.get("schema_version", 1)

        if input_schema == 1:
            migrated = cls._migrate_v1_to_v2(raw_data, segment_path)
            if isinstance(migrated, Err):
                return Err([f"[Shape] {e}" for e in migrated.error])
            canonical_data = migrated.value
        elif input_schema == 2:
            canonical_data = raw_data
        else:
            return Err([f"[Shape] Unsupported schema_version: {input_schema}"])

        skills_data = canonical_data.get("skills", [])
        if not isinstance(skills_data, list):
            return Err([f"[Shape] 'skills' must be a list, got {type(skills_data).__name__}"])

        canonical_skills: list[dict[str, object]] = []
        seen_ids: set[str] = set()
        seen_paths: set[str] = set()

        for i, raw_skill in enumerate(skills_data):
            if not isinstance(raw_skill, dict):
                errors.append(f"[Shape] Entry {i}: must be an object")
                continue

            if "canonical" not in raw_skill:
                errors.append(f"[Shape] Entry {i}: missing required field 'canonical'")
                continue

            skill_id = str(raw_skill.get("id", "")).strip()
            name = str(raw_skill.get("name", "")).strip()
            relative_path = str(raw_skill.get("relative_path", "")).strip()
            description = str(raw_skill.get("description", "")).strip()
            source = str(raw_skill.get("source", "")).strip()
            canonical = raw_skill.get("canonical")
            tags = raw_skill.get("tags", [])

            if not skill_id.startswith("skill:"):
                errors.append(f"[Shape] Entry {i}: id must start with 'skill:'")
            if not name:
                errors.append(f"[Shape] Entry {i}: missing required field 'name'")
            if not relative_path:
                errors.append(f"[Shape] Entry {i}: missing required field 'relative_path'")
            if not description:
                errors.append(f"[Shape] Entry {i}: missing required field 'description'")
            if not source:
                errors.append(f"[Shape] Entry {i}: missing required field 'source'")
            if not isinstance(canonical, bool):
                errors.append(f"[Shape] Entry {i}: 'canonical' must be boolean")

            if not relative_path or Path(relative_path).is_absolute() or ".." in Path(relative_path).parts:
                errors.append(f"[Shape] Entry {i}: invalid relative_path '{relative_path}'")
                continue

            if skill_id in seen_ids:
                errors.append(f"[Closure] Entry {i}: duplicate id '{skill_id}'")
            else:
                seen_ids.add(skill_id)

            if relative_path in seen_paths:
                errors.append(f"[Closure] Entry {i}: duplicate relative_path '{relative_path}'")
            else:
                seen_paths.add(relative_path)

            file_path = segment_path / relative_path
            if canonical is True and not file_path.exists():
                errors.append(f"[Closure] Entry {i}: canonical file not found: {relative_path}")

            canonical_skills.append(
                {
                    "id": skill_id,
                    "name": name,
                    "relative_path": relative_path,
                    "description": description,
                    "source": source,
                    "canonical": canonical,
                    "tags": tags if isinstance(tags, list) else [],
                }
            )

        if errors:
            return Err(errors)

        canonical_doc = {
            "schema_version": 2,
            "skills": canonical_skills,
        }

        canonical_entries: list[SkillManifestEntry] = []
        for skill_data in canonical_skills:
            relative_path = str(skill_data["relative_path"])
            file_path = segment_path / relative_path
            content_hash = cls._compute_content_hash(file_path)
            canonical_entries.append(
                SkillManifestEntry.from_dict(skill_data, content_hash)
            )

        return Ok(
            (
                cls(schema_version=2, skills=tuple(canonical_entries)),
                canonical_doc,
            )
        )

    @staticmethod
    def validate_pack_admission(
        manifest: "SkillManifest",
        *,
        declared_policy: str,
        pack_chunk_ids: list[str],
        pack_docs: list[str],
        pack_source_paths: list[str],
    ) -> Result[None, list[str]]:
        """Validate skill_hub pack admission checks at the policy boundary."""
        errors: list[str] = []

        if declared_policy != "skill_hub":
            errors.append("[Policy consistency] Promotion request must declare 'skill_hub'")

        if any(not chunk_id.startswith("skill:") for chunk_id in pack_chunk_ids):
            errors.append("[Shape] Pack contains non skill:* chunk IDs")

        if any(doc != "skill" for doc in pack_docs):
            errors.append("[Shape] Pack contains non-skill docs")

        manifest_paths = {
            skill.relative_path for skill in manifest.skills if skill.canonical
        }
        pack_paths = set(pack_source_paths)

        if pack_paths != manifest_paths:
            missing = sorted(manifest_paths - pack_paths)
            extra = sorted(pack_paths - manifest_paths)
            if missing:
                errors.append(f"[Closure] Missing pack entries for canonical manifest paths: {missing}")
            if extra:
                errors.append(f"[Closure] Pack contains non-canonical paths: {extra}")

        if errors:
            return Err(errors)
        return Ok(None)

    @staticmethod
    def _compute_content_hash(file_path: Path) -> str:
        """Compute SHA256 hash of file content."""
        content = file_path.read_text(encoding="utf-8")
        return hashlib.sha256(content.encode()).hexdigest()[:10]

    @classmethod
    def _migrate_v1_to_v2(
        cls, v1_data: dict[str, object], segment_path: Path
    ) -> Result[dict[str, object], list[str]]:
        """
        Migrate schema_version 1 to 2.

        v1 uses: source_path (absolute path to SKILL.md)
        v2 uses: relative_path (relative to segment root)

        Rejects ambiguous cases:
        - source_path not ending in /SKILL.md
        - derived file not found in segment
        """
        errors: list[str] = []
        skills_v2: list[dict[str, object]] = []

        skills_v1 = v1_data.get("skills", [])
        if not isinstance(skills_v1, list):
            return Err([f"'skills' must be a list, got {type(skills_v1).__name__}"])

        for i, skill in enumerate(skills_v1):
            if not isinstance(skill, dict):
                errors.append(f"Entry {i}: must be an object")
                continue

            source_path = skill.get("source_path", "")
            if not source_path:
                errors.append(f"Entry {i}: missing source_path")
                continue

            # Validate pattern: must end with /SKILL.md
            if not source_path.endswith("/SKILL.md"):
                errors.append(
                    f"Entry {i}: source_path must end with '/SKILL.md', got: {source_path}"
                )
                continue

            # Derive relative_path from source_path
            # /abs/path/to/skill-name/SKILL.md -> skill-name.md
            skill_dir = Path(source_path).parent.name
            if not skill_dir:
                errors.append(f"Entry {i}: cannot derive skill name from source_path")
                continue

            relative_path = f"{skill_dir}.md"

            # Validate file exists
            expected_file = segment_path / relative_path
            if not expected_file.exists():
                errors.append(f"Entry {i}: derived file not found: {relative_path}")
                continue

            # Generate stable skill_id
            skill_id = f"skill:{skill_dir}"

            # Build v2 entry
            skills_v2.append({
                "id": skill_id,
                "name": skill.get("name", skill_dir),
                "relative_path": relative_path,
                "description": skill.get("description", ""),
                "source": skill.get("source", "unknown"),
                "canonical": skill.get("canonical", True),
                "tags": skill.get("tags", []),
            })

        if errors:
            return Err(errors)

        return Ok({
            "schema_version": 2,
            "skills": skills_v2,
        })
