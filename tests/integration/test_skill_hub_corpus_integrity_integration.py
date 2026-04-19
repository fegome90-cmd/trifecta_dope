"""Integration tests for the Skill Hub Corpus Integrity Guard lifecycle."""

import json
from pathlib import Path
from typer.testing import CliRunner
import pytest

from src.infrastructure.cli import app
from src.application.use_cases import BuildContextPackUseCase
from src.infrastructure.file_system import FileSystemAdapter

def _make_segment(tmp_path: Path, name: str = "skills-hub") -> Path:
    segment = tmp_path / name
    segment.mkdir()
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    
    (segment / "skill.md").write_text("# Segment metadata\n")
    (segment / "AGENTS.md").write_text("# Agents Constitution\n")
    (segment / "GEMINI.md").write_text("# Gemini Constitution\n")
    
    (ctx_dir / f"agent_{name}.md").write_text("# Agent\n")
    (ctx_dir / f"prime_{name}.md").write_text("# Prime\n")
    (ctx_dir / f"session_{name}.md").write_text("# Session\n")
    
    return segment

def _write_config(segment: Path, required_sources: list[str]) -> None:
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    cfg = {
        "segment": segment.name,
        "scope": "test",
        "repo_root": str(segment),
        "indexing_policy": "skill_hub",
        "skill_hub_integrity": {
            "required_sources": required_sources,
            "allow_degraded": True,
        }
    }
    (ctx_dir / "trifecta_config.json").write_text(json.dumps(cfg))

def _write_manifest(segment: Path, sources: list[str]) -> None:
    skills = [
        {
            "id": f"skill:{i}",
            "name": f"Skill {i}",
            "relative_path": f"skill_{i}.md",
            "description": f"Skill {i}",
            "source": src,
            "canonical": True,
        }
        for i, src in enumerate(sources)
    ]
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    (ctx_dir / "skills_manifest.json").write_text(json.dumps({"schema_version": 2, "skills": skills}))
    for i, _ in enumerate(sources):
        (segment / f"skill_{i}.md").write_text(f"# Skill {i} content. We mention foo here.\n")

def test_integration_lifecycle_degraded(tmp_path: Path) -> None:
    # 1. Setup a segment missing required sources -> degraded state
    segment = _make_segment(tmp_path)
    # Give it only source-a, but expect source-a AND source-b
    _write_manifest(segment, ["source-a"])
    _write_config(segment, ["source-a", "source-b"])

    # 2. Build the context pack (should succeed, mark as degraded because allow_degraded=True)
    runner = CliRunner()
    result = runner.invoke(app, ["ctx", "sync", "--segment", str(segment)])
    assert result.exit_code == 0, result.output
    
    # Check receipt
    receipt_file = segment / "_ctx" / "skill_hub_promotion_receipt.json"
    assert receipt_file.exists(), result.output
    receipt = json.loads(receipt_file.read_text("utf-8"))
    assert receipt["publication_state"] == "degraded"
    
    # 3. Perform a search -> Should surface the warning
    search_result = runner.invoke(app, ["ctx", "search", "--segment", str(segment), "-q", "foo"])
    assert search_result.exit_code == 0
    assert "WARNING: Using degraded skill_hub corpus. Some required sources are missing." in search_result.output
    # Ensure there's a match found
    assert "Skill 0" in search_result.output

def test_integration_lifecycle_blocked(tmp_path: Path) -> None:
    # 1. Setup a segment missing required sources, but disallow degraded -> blocked state
    segment = _make_segment(tmp_path)
    _write_manifest(segment, ["source-a"])
    
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    cfg = {
        "segment": segment.name,
        "scope": "test",
        "repo_root": str(segment),
        "indexing_policy": "skill_hub",
        "skill_hub_integrity": {
            "required_sources": ["source-a", "source-b"],
            "allow_degraded": False, # Blocked!
        }
    }
    (ctx_dir / "trifecta_config.json").write_text(json.dumps(cfg))

    # 2. Build the context pack
    runner = CliRunner()
    result = runner.invoke(app, ["ctx", "sync", "--segment", str(segment)])
    
    # 3. Perform a search -> should fail because no valid promoted set was loaded
    search_result = runner.invoke(app, ["ctx", "search", "--segment", str(segment), "-q", "foo"])
    assert search_result.exit_code == 1
    assert "No valid promoted set" in search_result.output

def test_integration_lifecycle_healthy(tmp_path: Path) -> None:
    # 1. Setup a healthy segment
    segment = _make_segment(tmp_path)
    _write_manifest(segment, ["source-a", "source-b"])
    _write_config(segment, ["source-a", "source-b"])

    # 2. Build the context pack
    runner = CliRunner()
    result = runner.invoke(app, ["ctx", "sync", "--segment", str(segment)])
    assert result.exit_code == 0, result.output
    
    # Check receipt
    receipt_file = segment / "_ctx" / "skill_hub_promotion_receipt.json"
    assert receipt_file.exists(), result.output
    receipt = json.loads(receipt_file.read_text("utf-8"))
    assert receipt["publication_state"] == "healthy"
    
    # 3. Perform a search -> should succeed, no warnings
    search_result = runner.invoke(app, ["ctx", "search", "--segment", str(segment), "-q", "foo"])
    assert search_result.exit_code == 0
    assert "WARNING: Using degraded skill_hub corpus. Some required sources are missing." not in search_result.output
    # Ensure there's a match found
    assert "Skill 0" in search_result.output
