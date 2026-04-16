"""Tests for ContextService authority_state transport from receipt to read path.

Verifies that publication_state from the promotion receipt is correctly
carried through to SearchResult.authority_state for skill_hub segments.

Uses BuildContextPackUseCase to produce real promoted sets, then reads them
back through ContextService to verify authority_state transport end-to-end.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.application.context_service import ContextService
from src.application.use_cases import BuildContextPackUseCase
from src.domain.context_models import SearchResult
from src.domain.result import Ok
from src.infrastructure.file_system import FileSystemAdapter

# ---------------------------------------------------------------------------
# Test helpers (reuse the proven pattern from receipt tests)
# ---------------------------------------------------------------------------

_SKILL_HUB_PROMOTION_RECEIPT = "skill_hub_promotion_receipt.json"
_LAST_VALID_DIR = ".skill_hub_last_valid"


def _write_manifest(segment: Path, *, sources: list[str] | None = None) -> None:
    if sources is None:
        sources = ["pi-agent-skills"]
    skills = [
        {
            "id": f"skill:{i}",
            "name": f"Skill {i}",
            "relative_path": f"skill_{i}.md",
            "description": f"Skill {i} description",
            "source": src,
            "canonical": True,
        }
        for i, src in enumerate(sources)
    ]
    manifest = {"schema_version": 2, "skills": skills}
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    (ctx_dir / "skills_manifest.json").write_text(json.dumps(manifest))
    for i, _ in enumerate(sources):
        (segment / f"skill_{i}.md").write_text(f"# Skill {i}\n")


def _write_config(
    segment: Path,
    *,
    required_sources: list[str] | None = None,
    allow_degraded: bool = False,
) -> None:
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    integrity: dict[str, object] = {}
    if required_sources is not None:
        integrity = {
            "required_sources": required_sources,
            "allow_degraded": allow_degraded,
            "min_skills_per_source": 1,
        }
    config: dict[str, object] = {
        "segment": segment.name,
        "scope": "test",
        "repo_root": str(segment),
        "indexing_policy": "skill_hub",
    }
    if integrity:
        config["skill_hub_integrity"] = integrity
    (ctx_dir / "trifecta_config.json").write_text(json.dumps(config))


def _make_segment(tmp_path: Path, name: str = "skills-hub") -> Path:
    segment = tmp_path / name
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
    return segment


def _build(segment: Path) -> None:
    """Build promoted set via the real use case."""
    result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
    assert isinstance(result, Ok), f"Build failed: {result.error}"


def _receipt(segment: Path) -> dict[str, object]:
    return json.loads(
        (segment / "_ctx" / _SKILL_HUB_PROMOTION_RECEIPT).read_text()
    )


def _last_valid_receipt(segment: Path) -> dict[str, object]:
    return json.loads(
        (segment / "_ctx" / _LAST_VALID_DIR / _SKILL_HUB_PROMOTION_RECEIPT).read_text()
    )


# ---------------------------------------------------------------------------
# Healthy authority_state
# ---------------------------------------------------------------------------


class TestAuthorityStateHealthy:
    def test_healthy_promoted_set_exposes_healthy(self, tmp_path: Path) -> None:
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills", "claude-skills"])
        _write_config(segment, required_sources=["pi-agent-skills", "claude-skills"])
        _build(segment)

        assert _receipt(segment)["publication_state"] == "healthy"

        svc = ContextService(segment)
        result = svc.search("skill", k=5)

        assert isinstance(result, SearchResult)
        assert result.authority_state == "healthy"

    def test_no_guard_config_exposes_healthy(self, tmp_path: Path) -> None:
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_config(segment)  # no required_sources
        _build(segment)

        assert _receipt(segment)["publication_state"] == "healthy"

        svc = ContextService(segment)
        result = svc.search("skill", k=5)

        assert result.authority_state == "healthy"


# ---------------------------------------------------------------------------
# Degraded authority_state
# ---------------------------------------------------------------------------


class TestAuthorityStateDegraded:
    def test_degraded_promoted_set_exposes_degraded(self, tmp_path: Path) -> None:
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
            allow_degraded=True,
        )
        _build(segment)

        assert _receipt(segment)["publication_state"] == "degraded"

        svc = ContextService(segment)
        result = svc.search("skill", k=5)

        assert result.authority_state == "degraded"


# ---------------------------------------------------------------------------
# Fallback to last_valid
# ---------------------------------------------------------------------------


class TestAuthorityStateFallback:
    def test_fallback_to_last_valid_preserves_state(self, tmp_path: Path) -> None:
        """When live is invalid, fallback carries last_valid's authority_state."""
        segment = _make_segment(tmp_path)

        # Build a healthy promoted set → seals last_valid
        _write_manifest(segment, sources=["pi-agent-skills", "claude-skills"])
        _write_config(segment, required_sources=["pi-agent-skills", "claude-skills"])
        _build(segment)
        assert _receipt(segment)["publication_state"] == "healthy"

        # Verify last_valid was sealed
        lv_receipt = _last_valid_receipt(segment)
        assert lv_receipt["publication_state"] == "healthy"

        # Now corrupt the live set
        (segment / "_ctx" / "context_pack.json").unlink()

        # ContextService should fall back to last_valid
        svc = ContextService(segment)
        result = svc.search("skill", k=5)

        assert result.authority_state == "healthy"

    def test_fallback_to_degraded_last_valid(self, tmp_path: Path) -> None:
        """Fallback to a degraded last_valid shows degraded."""
        segment = _make_segment(tmp_path)

        # Build degraded set (writes live but does NOT seal last_valid)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
            allow_degraded=True,
        )
        _build(segment)
        assert _receipt(segment)["publication_state"] == "degraded"

        # No last_valid (degraded doesn't seal)
        assert not (segment / "_ctx" / _LAST_VALID_DIR).exists() or not (
            segment / "_ctx" / _LAST_VALID_DIR / _SKILL_HUB_PROMOTION_RECEIPT
        ).exists()

        # The live set itself is degraded
        svc = ContextService(segment)
        result = svc.search("skill", k=5)

        assert result.authority_state == "degraded"


# ---------------------------------------------------------------------------
# Missing / corrupt receipt
# ---------------------------------------------------------------------------


class TestAuthorityStateMissing:
    def test_no_publication_state_in_old_receipt_defaults_healthy(
        self, tmp_path: Path
    ) -> None:
        """Old receipt without publication_state field → defaults to healthy."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_config(segment)
        _build(segment)

        # Remove publication_state from receipt to simulate old format
        ctx_dir = segment / "_ctx"
        receipt = json.loads(
            (ctx_dir / _SKILL_HUB_PROMOTION_RECEIPT).read_text()
        )
        del receipt["publication_state"]
        (ctx_dir / _SKILL_HUB_PROMOTION_RECEIPT).write_text(json.dumps(receipt))

        svc = ContextService(segment)
        result = svc.search("skill", k=5)

        assert result.authority_state == "healthy"

    def test_corrupt_receipt_raises_runtime_error(self, tmp_path: Path) -> None:
        """Both live and backup corrupt → RuntimeError, no silent success."""
        segment = _make_segment(tmp_path)
        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir(parents=True, exist_ok=True)

        (ctx_dir / _SKILL_HUB_PROMOTION_RECEIPT).write_text("{bad json")
        (ctx_dir / "skills_manifest.json").write_text("{}")
        (ctx_dir / "context_pack.json").write_text("{}")
        (ctx_dir / "trifecta_config.json").write_text(
            json.dumps(
                {
                    "segment": segment.name,
                    "scope": "test",
                    "repo_root": str(segment),
                    "indexing_policy": "skill_hub",
                }
            )
        )

        svc = ContextService(segment)

        with pytest.raises(RuntimeError, match="No valid promoted set"):
            svc.search("test", k=5)
