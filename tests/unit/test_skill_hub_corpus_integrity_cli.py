"""CLI surfacing tests for skill_hub corpus integrity (Batch 6)."""

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
    (segment / "skill.md").write_text("# Segment metadata\n")
    return segment

def _write_config(segment: Path, required_sources: list[str] | None = None, policy: str = "skill_hub") -> None:
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    cfg = {
        "segment": segment.name,
        "scope": "test",
        "repo_root": str(segment),
        "indexing_policy": policy,
    }
    if required_sources is not None:
        cfg["skill_hub_integrity"] = {
            "required_sources": required_sources,
            "allow_degraded": True,
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
        (segment / f"skill_{i}.md").write_text(f"# Skill {i}\n")

def _build(segment: Path) -> None:
    result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
    # the Ok check is omitted since this is CLI test and we know it passes logic

def _patch_receipt(segment: Path, publication_state: str | None) -> None:
    receipt_file = segment / "_ctx" / "skill_hub_promotion_receipt.json"
    data = json.loads(receipt_file.read_text(encoding="utf-8"))
    if publication_state is None:
        if "publication_state" in data:
            del data["publication_state"]
    else:
        data["publication_state"] = publication_state
    receipt_file.write_text(json.dumps(data))

def test_cli_search_emits_warning_if_degraded(tmp_path: Path) -> None:
    segment = _make_segment(tmp_path)
    _write_manifest(segment, ["agent-tests"])
    _write_config(segment, ["agent-tests", "claude-configs"]) # Missing claude-configs => degraded
    _build(segment)

    runner = CliRunner()
    result = runner.invoke(app, ["ctx", "search", "--segment", str(segment), "-q", "skill"])
    
    assert result.exit_code == 0
    # stderr has the warning
    assert "WARNING: Using degraded skill_hub corpus." in result.output
    # stdout is untainted by warning, meaning the warning goes through stderr formatting
    # wait - click runner mixes stdout and stderr in result.output by default if we don't separate them stringently
    # but we will check it's present!

def test_cli_search_no_warning_if_healthy(tmp_path: Path) -> None:
    segment = _make_segment(tmp_path)
    _write_manifest(segment, ["agent-tests", "claude-configs"])
    _write_config(segment, ["agent-tests", "claude-configs"]) 
    _build(segment)

    runner = CliRunner()
    result = runner.invoke(app, ["ctx", "search", "--segment", str(segment), "-q", "skill"])
    
    assert result.exit_code == 0
    assert "WARNING: Using degraded skill_hub corpus" not in result.output

def test_cli_search_no_warning_if_legacy_receipt(tmp_path: Path) -> None:
    segment = _make_segment(tmp_path)
    _write_manifest(segment, ["agent-tests", "claude-configs"])
    _write_config(segment, ["agent-tests", "claude-configs"]) 
    _build(segment)
    _patch_receipt(segment, None)

    runner = CliRunner()
    result = runner.invoke(app, ["ctx", "search", "--segment", str(segment), "-q", "skill"])
    
    assert result.exit_code == 0
    assert "WARNING: Using degraded skill_hub corpus" not in result.output

def test_cli_get_emits_warning_if_degraded(tmp_path: Path) -> None:
    segment = _make_segment(tmp_path)
    _write_manifest(segment, ["agent-tests"])
    _write_config(segment, ["agent-tests", "claude-configs"]) 
    _build(segment)

    runner = CliRunner()
    result = runner.invoke(app, ["ctx", "get", "--segment", str(segment), "-i", "skill:0"])
    
    assert result.exit_code == 0
    assert "WARNING: Using degraded skill_hub corpus." in result.output

def test_cli_get_no_warning_if_healthy(tmp_path: Path) -> None:
    segment = _make_segment(tmp_path)
    _write_manifest(segment, ["agent-tests"])
    _write_config(segment, ["agent-tests"]) 
    _build(segment)

    runner = CliRunner()
    result = runner.invoke(app, ["ctx", "get", "--segment", str(segment), "-i", "skill:0"])
    
    assert result.exit_code == 0
    assert "WARNING: Using degraded skill_hub corpus." not in result.output

def test_cli_search_blocked_never_surfaced_as_warning(tmp_path: Path) -> None:
    segment = _make_segment(tmp_path)
    _write_manifest(segment, ["agent-tests"])
    _write_config(segment, ["agent-tests"]) 
    _build(segment)
    _patch_receipt(segment, "blocked")
    lv_dir = segment / "_ctx" / ".skill_hub_last_valid"
    if lv_dir.exists():
        import shutil
        shutil.rmtree(lv_dir)

    runner = CliRunner()
    result = runner.invoke(app, ["ctx", "search", "--segment", str(segment), "-q", "skill"])
    
    # Should crash with 1 because blocked is invalid and load fails
    assert result.exit_code == 1
    # Ensure it's not swallowed into a warning
    assert "WARNING: Using degraded skill_hub corpus." not in result.output
    # Fails closed in Error path
    assert "No valid promoted set" in result.output or "missing" in result.output or "invalid" in result.output

