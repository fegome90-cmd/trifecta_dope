"""Phase B promoted-set sealing tests for skill_hub change."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.application.use_cases import BuildContextPackUseCase
from src.domain.result import Err, Ok
from src.infrastructure.file_system import FileSystemAdapter
from src.infrastructure.file_system_utils import AtomicWriter


def _write_skill_hub_config(segment: Path, *, policy: str = "skill_hub") -> None:
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    (ctx_dir / "trifecta_config.json").write_text(
        json.dumps(
            {
                "segment": segment.name,
                "scope": "test",
                "repo_root": str(segment),
                "indexing_policy": policy,
            }
        )
    )


def _write_manifest(segment: Path, *, description: str = "Skill A") -> None:
    manifest = {
        "schema_version": 2,
        "skills": [
            {
                "id": "skill:a",
                "name": "a",
                "relative_path": "a.md",
                "description": description,
                "source": "test",
                "canonical": True,
            }
        ],
    }
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    (ctx_dir / "skills_manifest.json").write_text(json.dumps(manifest))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_skill_hub_promotion_publishes_canonical_manifest_pack_and_receipt(tmp_path: Path) -> None:
    """Promotion publishes one sealed artifact set with provenance fingerprints."""
    segment = tmp_path / "skills-hub"
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
    (segment / "a.md").write_text("# A\n")
    _write_skill_hub_config(segment)
    _write_manifest(segment)

    result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)

    assert isinstance(result, Ok)
    ctx_dir = segment / "_ctx"
    manifest_path = ctx_dir / "skills_manifest.json"
    pack_path = ctx_dir / "context_pack.json"
    receipt_path = ctx_dir / "skill_hub_promotion_receipt.json"
    assert manifest_path.exists()
    assert pack_path.exists()
    assert receipt_path.exists()

    receipt = json.loads(receipt_path.read_text())
    assert receipt["schema_version"] == 1
    assert receipt["policy"] == "skill_hub"
    assert receipt["segment_id"] == result.value.segment
    assert receipt["manifest_fingerprint"] == _sha256(manifest_path)
    assert receipt["pack_fingerprint"] == _sha256(pack_path)


def test_skill_hub_promotion_restores_last_valid_set_when_receipt_write_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Failed publication must preserve the previously promoted valid set."""
    segment = tmp_path / "skills-hub"
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
    (segment / "a.md").write_text("# A v1\n")
    _write_skill_hub_config(segment)
    _write_manifest(segment, description="v1")

    first = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
    assert isinstance(first, Ok)

    ctx_dir = segment / "_ctx"
    manifest_path = ctx_dir / "skills_manifest.json"
    pack_path = ctx_dir / "context_pack.json"
    receipt_path = ctx_dir / "skill_hub_promotion_receipt.json"
    previous_manifest = manifest_path.read_text()
    previous_pack = pack_path.read_text()
    previous_receipt = receipt_path.read_text()

    (segment / "a.md").write_text("# A v2\n")
    _write_manifest(segment, description="v2")

    original_write = AtomicWriter.write

    def failing_write(path: Path, content: str) -> None:
        if path.name == "skill_hub_promotion_receipt.json":
            raise OSError("simulated receipt write failure")
        original_write(path, content)

    monkeypatch.setattr(AtomicWriter, "write", staticmethod(failing_write))

    failed = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
    assert isinstance(failed, Err)
    assert any("promotion" in err.lower() for err in failed.error)

    assert manifest_path.read_text() == previous_manifest
    assert pack_path.read_text() == previous_pack
    assert receipt_path.read_text() == previous_receipt
