"""Receipt + publication-state contract tests for skill-hub-corpus-integrity-guard.

Tests for BuildContextPackUseCase with integrity guard enabled:
    - blocked: no live artifact written, no last_valid overwrite
    - degraded: live artifacts written, last_valid NOT sealed
    - healthy: live artifacts written, last_valid sealed

Also verifies the receipt JSON carries the full ``integrity`` block.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.application.use_cases import BuildContextPackUseCase
from src.domain.result import Err, Ok
from src.infrastructure.file_system import FileSystemAdapter

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

_SKILL_HUB_PROMOTION_RECEIPT = "skill_hub_promotion_receipt.json"
_LAST_VALID_DIR = ".skill_hub_last_valid"


def _write_skill_hub_config(
    segment: Path,
    *,
    required_sources: list[str] | None = None,
    allow_degraded: bool = False,
    min_skills_per_source: int = 1,
) -> None:
    """Write a trifecta_config.json with integrity policy."""
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    integrity: dict[str, object] = {}
    if required_sources is not None:
        integrity = {
            "required_sources": required_sources,
            "allow_degraded": allow_degraded,
            "min_skills_per_source": min_skills_per_source,
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


def _write_manifest(
    segment: Path,
    *,
    sources: list[str] | None = None,
) -> None:
    """Write a minimal skills_manifest.json with controllable per-skill sources."""
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
    # create stub skill files that the indexer expects
    for i, _ in enumerate(sources):
        (segment / f"skill_{i}.md").write_text(f"# Skill {i}\n")


def _make_segment(tmp_path: Path, name: str = "skills-hub") -> Path:
    segment = tmp_path / name
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
    return segment


def _receipt(segment: Path) -> dict[str, object]:
    receipt_path = segment / "_ctx" / _SKILL_HUB_PROMOTION_RECEIPT
    return json.loads(receipt_path.read_text())  # type: ignore[return-value]


def _last_valid_exists(segment: Path) -> bool:
    lv = segment / "_ctx" / _LAST_VALID_DIR
    return (
        (lv / "skills_manifest.json").exists()
        and (lv / "context_pack.json").exists()
        and (lv / _SKILL_HUB_PROMOTION_RECEIPT).exists()
    )


# ---------------------------------------------------------------------------
# Blocked: no publication at all
# ---------------------------------------------------------------------------


class TestBlockedVerdict:
    def test_blocked_returns_err(self, tmp_path: Path) -> None:
        """A corpus missing required sources must return Err and NOT publish."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
            allow_degraded=False,
        )

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)

        assert isinstance(result, Err)
        assert any("blocked" in e.lower() or "missing" in e.lower() for e in result.error)

    def test_blocked_does_not_write_live_receipt(self, tmp_path: Path) -> None:
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
            allow_degraded=False,
        )

        BuildContextPackUseCase(FileSystemAdapter()).execute(segment)

        receipt_path = segment / "_ctx" / _SKILL_HUB_PROMOTION_RECEIPT
        assert not receipt_path.exists(), (
            "Blocked promotion must not write the live receipt"
        )

    def test_blocked_does_not_overwrite_existing_last_valid(self, tmp_path: Path) -> None:
        """An existing last_valid set must survive a blocked attempt."""
        segment = _make_segment(tmp_path)

        # First: healthy promotion → seals last_valid
        _write_manifest(segment, sources=["pi-agent-skills", "claude-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
            allow_degraded=False,
        )
        first = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(first, Ok)
        assert _last_valid_exists(segment)

        # Capture last_valid content before the blocked attempt
        lv_dir = segment / "_ctx" / _LAST_VALID_DIR
        lv_receipt_before = (lv_dir / _SKILL_HUB_PROMOTION_RECEIPT).read_text()

        # Second: corpus collapses → blocked
        _write_manifest(segment, sources=["pi-agent-skills"])  # claude-skills gone
        blocked = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(blocked, Err)

        # last_valid receipt must be unchanged
        lv_receipt_after = (lv_dir / _SKILL_HUB_PROMOTION_RECEIPT).read_text()
        assert lv_receipt_before == lv_receipt_after, (
            "Blocked attempt must not overwrite last_valid receipt"
        )

    def test_blocked_error_contains_missing_sources(self, tmp_path: Path) -> None:
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills", "codex-skills"],
            allow_degraded=False,
        )

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)

        assert isinstance(result, Err)
        full_error = " ".join(result.error)
        assert "claude-skills" in full_error or "codex-skills" in full_error


# ---------------------------------------------------------------------------
# Degraded: live published but last_valid NOT sealed
# ---------------------------------------------------------------------------


class TestDegradedVerdict:
    def test_degraded_returns_ok(self, tmp_path: Path) -> None:
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
            allow_degraded=True,
        )

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)

        assert isinstance(result, Ok)

    def test_degraded_writes_live_artifacts(self, tmp_path: Path) -> None:
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
            allow_degraded=True,
        )

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(result, Ok)

        ctx_dir = segment / "_ctx"
        assert (ctx_dir / "skills_manifest.json").exists()
        assert (ctx_dir / "context_pack.json").exists()
        assert (ctx_dir / _SKILL_HUB_PROMOTION_RECEIPT).exists()

    def test_degraded_does_not_seal_last_valid(self, tmp_path: Path) -> None:
        """Degraded publication must NOT create or update .skill_hub_last_valid."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
            allow_degraded=True,
        )

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(result, Ok)

        assert not _last_valid_exists(segment), (
            "Degraded publication must not seal .skill_hub_last_valid"
        )

    def test_degraded_does_not_overwrite_existing_last_valid(self, tmp_path: Path) -> None:
        """An existing healthy last_valid must survive a degraded publish."""
        segment = _make_segment(tmp_path)

        # First: healthy → seals last_valid
        _write_manifest(segment, sources=["pi-agent-skills", "claude-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
            allow_degraded=True,
        )
        first = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(first, Ok)
        assert _last_valid_exists(segment)

        lv_dir = segment / "_ctx" / _LAST_VALID_DIR
        lv_receipt_before = (lv_dir / _SKILL_HUB_PROMOTION_RECEIPT).read_text()

        # Second: degraded publish — only pi-agent-skills present
        _write_manifest(segment, sources=["pi-agent-skills"])
        degraded = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(degraded, Ok)

        lv_receipt_after = (lv_dir / _SKILL_HUB_PROMOTION_RECEIPT).read_text()
        assert lv_receipt_before == lv_receipt_after, (
            "Degraded publish must not overwrite existing healthy last_valid"
        )

    def test_degraded_receipt_has_correct_publication_state(self, tmp_path: Path) -> None:
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
            allow_degraded=True,
        )

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(result, Ok)

        r = _receipt(segment)
        assert r["publication_state"] == "degraded"


# ---------------------------------------------------------------------------
# Healthy: live published AND last_valid sealed
# ---------------------------------------------------------------------------


class TestHealthyVerdict:
    def test_healthy_returns_ok(self, tmp_path: Path) -> None:
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills", "claude-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
        )

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)

        assert isinstance(result, Ok)

    def test_healthy_seals_last_valid(self, tmp_path: Path) -> None:
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills", "claude-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
        )

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(result, Ok)

        assert _last_valid_exists(segment), (
            "Healthy promotion must seal .skill_hub_last_valid"
        )

    def test_healthy_receipt_has_correct_publication_state(self, tmp_path: Path) -> None:
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills", "claude-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
        )

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(result, Ok)

        r = _receipt(segment)
        assert r["publication_state"] == "healthy"

    def test_no_guard_configured_always_healthy(self, tmp_path: Path) -> None:
        """If required_sources is empty (default), promotion is always healthy."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_skill_hub_config(segment)  # no integrity config = guard disabled

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)

        assert isinstance(result, Ok)
        assert _last_valid_exists(segment)


# ---------------------------------------------------------------------------
# Receipt integrity block contract
# ---------------------------------------------------------------------------


class TestReceiptIntegrityBlock:
    _REQUIRED_INTEGRITY_KEYS = {
        "verdict",
        "observed_skill_count",
        "observed_source_count",
        "observed_counts",
        "missing_sources",
        "required_sources",
        "min_skills_per_source",
        "reason_code",
        "manifest_fingerprint",
        "corpus_hash",
    }

    def test_receipt_contains_integrity_block_when_guard_configured(
        self, tmp_path: Path
    ) -> None:
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills", "claude-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
        )

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(result, Ok)

        r = _receipt(segment)
        assert "integrity" in r, "Receipt must include 'integrity' block when guard is active"

    def test_integrity_block_contains_all_required_keys(self, tmp_path: Path) -> None:
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills", "claude-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
        )

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(result, Ok)

        r = _receipt(segment)
        integrity = r["integrity"]
        assert isinstance(integrity, dict)
        missing_keys = self._REQUIRED_INTEGRITY_KEYS - set(integrity.keys())
        assert not missing_keys, f"Integrity block missing keys: {missing_keys}"

    def test_integrity_block_verdict_matches_publication_state(
        self, tmp_path: Path
    ) -> None:
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
            allow_degraded=True,
        )

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(result, Ok)

        r = _receipt(segment)
        assert r["publication_state"] == r["integrity"]["verdict"]  # type: ignore[index]

    def test_integrity_block_missing_sources_reflects_config(
        self, tmp_path: Path
    ) -> None:
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
            allow_degraded=True,
        )

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(result, Ok)

        r = _receipt(segment)
        integrity = r["integrity"]
        assert isinstance(integrity, dict)
        assert "claude-skills" in integrity["missing_sources"]

    def test_integrity_block_contains_corpus_hash_and_fingerprint(
        self, tmp_path: Path
    ) -> None:
        """Receipt integrity block must carry corpus_hash and manifest_fingerprint."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills", "claude-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
        )

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(result, Ok)

        r = _receipt(segment)
        integrity = r["integrity"]
        assert isinstance(integrity, dict)
        assert "corpus_hash" in integrity, "integrity block must include corpus_hash"
        assert "manifest_fingerprint" in integrity, (
            "integrity block must include manifest_fingerprint"
        )
        assert len(integrity["corpus_hash"]) == 16, "corpus_hash must be 16 hex chars"

    def test_receipt_without_guard_still_valid_schema(self, tmp_path: Path) -> None:
        """Without required_sources, receipt is still valid and includes integrity block."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_skill_hub_config(segment)  # no required_sources

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(result, Ok)

        r = _receipt(segment)
        assert r["schema_version"] == 1
        assert r["policy"] == "skill_hub"
        # Integrity block is present with no-guard healthy verdict
        assert r["publication_state"] == "healthy"

    def test_receipt_without_guard_has_no_integrity_block(self, tmp_path: Path) -> None:
        """Without required_sources, receipt still has integrity block (no-guard verdict)."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_skill_hub_config(segment)

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(result, Ok)

        r = _receipt(segment)
        # Integrity block IS present even without guard — it records the no-guard verdict
        assert "integrity" in r
        assert r["integrity"]["verdict"] == "healthy"
        assert r["publication_state"] == "healthy"


# ---------------------------------------------------------------------------
# No-guard backward compat: existing tests must still pass
# ---------------------------------------------------------------------------


class TestBackwardCompatNoGuard:
    def test_existing_promotion_without_integrity_config_still_works(
        self, tmp_path: Path
    ) -> None:
        """Existing segments without skill_hub_integrity in config must still work."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        # Write config WITHOUT skill_hub_integrity key
        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir(parents=True, exist_ok=True)
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

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)

        assert isinstance(result, Ok)
        assert _last_valid_exists(segment), "Default (no-guard) must seal last_valid"


# ---------------------------------------------------------------------------
# Config load failure: must NEVER produce healthy
# ---------------------------------------------------------------------------


class TestConfigLoadFailure:
    """Config load failure must block promotion — never silently pass as healthy."""

    def test_corrupt_config_blocks_promotion(self, tmp_path: Path) -> None:
        """Corrupt trifecta_config.json must return Err, not healthy."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills", "claude-skills"])
        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir(parents=True, exist_ok=True)
        # Write invalid JSON
        (ctx_dir / "trifecta_config.json").write_text("{not valid json}")

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)

        assert isinstance(result, Err), (
            "Corrupt config must block promotion, not silently pass"
        )
        # Corrupt JSON is caught either at segment canon validation or at
        # integrity config load — both paths must produce Err.
        assert not isinstance(result, Ok)

    def test_missing_config_blocks_promotion(self, tmp_path: Path) -> None:
        """Missing trifecta_config.json must return Err, not healthy."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        # Ensure _ctx exists but NO trifecta_config.json
        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir(parents=True, exist_ok=True)
        # Remove config if it exists
        config_path = ctx_dir / "trifecta_config.json"
        if config_path.exists():
            config_path.unlink()

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)

        assert isinstance(result, Err), (
            "Missing config must block promotion, not silently pass"
        )

    def test_config_load_failure_does_not_write_receipt(self, tmp_path: Path) -> None:
        """Corrupt config must not produce any receipt artifact."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir(parents=True, exist_ok=True)
        (ctx_dir / "trifecta_config.json").write_text("{")

        BuildContextPackUseCase(FileSystemAdapter()).execute(segment)

        receipt_path = ctx_dir / _SKILL_HUB_PROMOTION_RECEIPT
        assert not receipt_path.exists(), (
            "Config load failure must not write receipt"
        )

    def test_healthy_requires_real_evaluation(self, tmp_path: Path) -> None:
        """healthy verdict must come from actual evaluation, not from config failure bypass."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills", "claude-skills"])
        _write_skill_hub_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
        )

        result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
        assert isinstance(result, Ok)

        r = _receipt(segment)
        assert r["publication_state"] == "healthy"
        assert r["integrity"]["verdict"] == "healthy"
        assert r["integrity"]["reason_code"] == "all_required_sources_present"
        assert r["integrity"]["missing_sources"] == []
