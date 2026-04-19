"""SearchResult authority_state threading tests (Batch 4).

Validates that ContextService correctly threads the loaded authority_state into
SearchResult, and that SearchResult exposes it correctly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.application.context_service import ContextService
from src.application.use_cases import BuildContextPackUseCase
from src.domain.context_models import SearchResult, SearchHit
from src.domain.result import Ok
from src.infrastructure.file_system import FileSystemAdapter

# ---------------------------------------------------------------------------
# Shared fixture helpers
# ---------------------------------------------------------------------------

def _make_segment(tmp_path: Path, name: str = "skills-hub") -> Path:
    segment = tmp_path / name
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
    return segment

def _write_config(
    segment: Path,
    *,
    required_sources: list[str] | None = None,
    allow_degraded: bool = False,
    policy: str = "skill_hub",
) -> None:
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    cfg: dict[str, object] = {
        "segment": segment.name,
        "scope": "test",
        "repo_root": str(segment),
        "indexing_policy": policy,
    }
    if required_sources is not None:
        cfg["skill_hub_integrity"] = {
            "required_sources": required_sources,
            "allow_degraded": allow_degraded,
        }
    (ctx_dir / "trifecta_config.json").write_text(json.dumps(cfg))

def _write_manifest(segment: Path, *, sources: list[str] | None = None) -> None:
    if sources is None:
        sources = ["pi-agent-skills"]
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
    assert isinstance(result, Ok)

def _patch_receipt(receipt_path: Path, *, publication_state: str | None) -> None:
    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    if publication_state is None:
        data.pop("publication_state", None)
    else:
        data["publication_state"] = publication_state
    receipt_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# SearchResult model tests
# ---------------------------------------------------------------------------

def test_search_result_default_authority_state_is_healthy() -> None:
    """SearchResult.authority_state defaults to healthy."""
    result = SearchResult(hits=[])
    assert result.authority_state == "healthy"

def test_search_result_accepts_degraded_state() -> None:
    """SearchResult can be constructed with degraded state."""
    result = SearchResult(hits=[], authority_state="degraded")
    assert result.authority_state == "degraded"

# ---------------------------------------------------------------------------
# Threading from ContextService tests
# ---------------------------------------------------------------------------

def test_search_threads_healthy_state(tmp_path: Path) -> None:
    """A healthy promoted set results in SearchResult with authority_state='healthy'."""
    segment = _make_segment(tmp_path)
    _write_manifest(segment, sources=["pi-agent-skills", "claude-skills"])
    _write_config(segment, required_sources=["pi-agent-skills", "claude-skills"])
    _build(segment)

    service = ContextService(segment)
    result = service.search("skill")

    assert isinstance(result, SearchResult)
    assert result.authority_state == "healthy"

def test_search_threads_degraded_state(tmp_path: Path) -> None:
    """A degraded promoted set results in SearchResult with authority_state='degraded'."""
    segment = _make_segment(tmp_path)
    _write_manifest(segment, sources=["pi-agent-skills"])
    _write_config(segment, required_sources=["pi-agent-skills", "claude-skills"], allow_degraded=True)
    _build(segment)

    service = ContextService(segment)
    result = service.search("skill")

    assert isinstance(result, SearchResult)
    assert result.authority_state == "degraded"

def test_legacy_receipt_threads_healthy_state(tmp_path: Path) -> None:
    """A receipt without publication_state threads 'healthy' to SearchResult."""
    segment = _make_segment(tmp_path)
    _write_manifest(segment)
    _write_config(segment)
    _build(segment)

    _patch_receipt(segment / "_ctx" / "skill_hub_promotion_receipt.json", publication_state=None)

    service = ContextService(segment)
    result = service.search("skill")

    assert isinstance(result, SearchResult)
    assert result.authority_state == "healthy"

def test_non_skill_hub_policy_threads_healthy_state(tmp_path: Path) -> None:
    """Non-skill_hub segments return healthy implicitly."""
    segment = _make_segment(tmp_path)
    # Simple context setup without skill_hub builder
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir()
    _write_config(segment, policy="standard") # Not skill-hub
    pack = {
        "schema_version": 1,
        "segment": segment.name,
        "chunks": [],
        "index": []
    }
    (ctx_dir / "context_pack.json").write_text(json.dumps(pack))

    service = ContextService(segment)
    result = service.search("skill")

    assert isinstance(result, SearchResult)
    assert result.authority_state == "healthy", "Non-skill-hub should default to healthy"

def test_blocked_receipt_never_transported(tmp_path: Path) -> None:
    """Blocked receipt cannot be loaded and therefore cannot pass its state to SearchResult."""
    segment = _make_segment(tmp_path)
    _write_manifest(segment)
    _write_config(segment)
    _build(segment)

    lv_dir = segment / "_ctx" / ".skill_hub_last_valid"
    for p in lv_dir.iterdir(): p.unlink()
    lv_dir.rmdir()

    _patch_receipt(segment / "_ctx" / "skill_hub_promotion_receipt.json", publication_state="blocked")

    service = ContextService(segment)
    with pytest.raises(RuntimeError):
         service.search("skill")
