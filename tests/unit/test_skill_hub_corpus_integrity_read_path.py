"""Read-path authority_state tests for skill-hub-corpus-integrity-guard (Batch 3).

Validates that ContextService._load_skill_hub_promoted_pack correctly:
    - Reads publication_state from the live receipt and exposes it as authority_state
    - Falls back to last_valid and exposes THAT set's authority_state (not the live one)
    - Defaults to "healthy" for legacy receipts without `publication_state`
    - Rejects "blocked" receipts as inadmissible rather than normalising them

Scope: context_service.py read path only.
Not tested here: SearchResult threading, CLI warnings (Batches 4-6 scope).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.application.context_service import ContextService
from src.application.use_cases import BuildContextPackUseCase
from src.domain.result import Ok
from src.infrastructure.file_system import FileSystemAdapter

# ---------------------------------------------------------------------------
# Shared fixture helpers (mirroring phase_b/c patterns — no new public fixtures)
# ---------------------------------------------------------------------------

_RECEIPT = "skill_hub_promotion_receipt.json"
_LAST_VALID = ".skill_hub_last_valid"


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
) -> None:
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    cfg: dict[str, object] = {
        "segment": segment.name,
        "scope": "test",
        "repo_root": str(segment),
        "indexing_policy": "skill_hub",
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
    assert isinstance(result, Ok), f"Promotion failed: {result}"  # type: ignore[union-attr]


def _patch_receipt(receipt_path: Path, *, publication_state: str | None) -> None:
    """Rewrite the receipt publication_state in-place without invalidating fingerprints.

    IMPORTANT: We patch WITHOUT touching manifest/pack so fingerprints remain valid.
    We need to patch BOTH the receipt file AND re-seal fingerprints because the
    receipt itself is not fingerprinted — only manifest and pack are.
    """
    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    if publication_state is None:
        data.pop("publication_state", None)  # simulate legacy receipt
    else:
        data["publication_state"] = publication_state
    receipt_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Live healthy → authority_state = "healthy"
# ---------------------------------------------------------------------------


class TestLiveHealthy:
    def test_live_healthy_authority_state(self, tmp_path: Path) -> None:
        """search() on a live healthy promoted set returns authority_state='healthy'."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills", "claude-skills"])
        _write_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
        )
        _build(segment)

        service = ContextService(segment)
        result = service.search("skill", k=5)

        assert result.authority_state == "healthy"

    def test_live_healthy_no_guard_authority_state(self, tmp_path: Path) -> None:
        """No guard configured → always healthy → authority_state='healthy'."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment)
        _write_config(segment)  # no required_sources
        _build(segment)

        service = ContextService(segment)
        result = service.search("skill", k=5)

        assert result.authority_state == "healthy"


# ---------------------------------------------------------------------------
# Live degraded → authority_state = "degraded"
# ---------------------------------------------------------------------------


class TestLiveDegraded:
    def test_live_degraded_authority_state(self, tmp_path: Path) -> None:
        """search() on a live degraded promoted set returns authority_state='degraded'."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment, sources=["pi-agent-skills"])
        _write_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
            allow_degraded=True,
        )
        _build(segment)

        service = ContextService(segment)
        result = service.search("skill", k=5)

        assert result.authority_state == "degraded"


# ---------------------------------------------------------------------------
# Fallback (last_valid) → authority_state reflects last_valid receipt
# ---------------------------------------------------------------------------


class TestFallbackAuthority:
    def _build_healthy_with_last_valid(self, segment: Path) -> None:
        """Build a healthy set that seals last_valid, then corrupt live."""
        _write_manifest(segment, sources=["pi-agent-skills", "claude-skills"])
        _write_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
        )
        _build(segment)

    def _corrupt_live_receipt(self, segment: Path) -> None:
        receipt_path = segment / "_ctx" / _RECEIPT
        receipt_path.write_text("{invalid json}", encoding="utf-8")

    def test_fallback_last_valid_healthy_authority_state(self, tmp_path: Path) -> None:
        """When live set is inadmissible, fallback last_valid healthy → authority_state='healthy'."""
        segment = _make_segment(tmp_path)
        self._build_healthy_with_last_valid(segment)
        self._corrupt_live_receipt(segment)

        service = ContextService(segment)
        result = service.search("skill", k=5)

        assert result.authority_state == "healthy"

    def test_fallback_respects_last_valid_receipt_state_not_live(
        self, tmp_path: Path
    ) -> None:
        """authority_state from fallback must come from last_valid receipt, NOT live."""
        segment = _make_segment(tmp_path)
        # Build healthy → seals last_valid as "healthy"
        self._build_healthy_with_last_valid(segment)
        # Corrupt the live receipt so loader falls back
        self._corrupt_live_receipt(segment)
        # Patch last_valid receipt to "degraded" to verify we read from fallback
        lv_receipt = segment / "_ctx" / _LAST_VALID / _RECEIPT
        _patch_receipt(lv_receipt, publication_state="degraded")

        service = ContextService(segment)
        result = service.search("skill", k=5)

        assert result.authority_state == "degraded", (
            "authority_state must reflect the last_valid receipt, not the (invalid) live one"
        )

    def test_fallback_last_valid_degraded_authority_state(self, tmp_path: Path) -> None:
        """Fallback to last_valid with degraded state → authority_state='degraded'."""
        segment = _make_segment(tmp_path)
        self._build_healthy_with_last_valid(segment)
        self._corrupt_live_receipt(segment)
        lv_receipt = segment / "_ctx" / _LAST_VALID / _RECEIPT
        _patch_receipt(lv_receipt, publication_state="degraded")

        service = ContextService(segment)
        result = service.search("skill", k=5)

        assert result.authority_state == "degraded"


# ---------------------------------------------------------------------------
# Legacy receipts without `publication_state`
# ---------------------------------------------------------------------------


class TestLegacyReceiptCompat:
    def test_legacy_receipt_without_publication_state_defaults_to_healthy(
        self, tmp_path: Path
    ) -> None:
        """Backward compat: receipt without publication_state → authority_state='healthy'.

        This is intentional legacy-only behavior, NOT a new contract.
        New code must always write publication_state explicitly.
        """
        segment = _make_segment(tmp_path)
        _write_manifest(segment)
        _write_config(segment)
        _build(segment)

        # Strip publication_state from the receipt (simulate legacy format)
        receipt_path = segment / "_ctx" / _RECEIPT
        _patch_receipt(receipt_path, publication_state=None)

        service = ContextService(segment)
        result = service.search("skill", k=5)

        assert result.authority_state == "healthy", (
            "Legacy receipts without publication_state must default to 'healthy' "
            "(backward compatibility only — not a contract for new code)"
        )

    def test_legacy_receipt_none_publication_state_explicitly_documented(
        self, tmp_path: Path
    ) -> None:
        """Verifies the default is 'healthy', not None, not 'unknown', not 'degraded'."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment)
        _write_config(segment)
        _build(segment)

        receipt_path = segment / "_ctx" / _RECEIPT
        _patch_receipt(receipt_path, publication_state=None)
        # Verify the patch actually removed the field
        data = json.loads(receipt_path.read_text())
        assert "publication_state" not in data, "Test setup: field should be absent"

        result = ContextService(segment).search("skill", k=5)

        assert result.authority_state == "healthy"
        assert result.authority_state != "degraded"
        assert result.authority_state is not None


# ---------------------------------------------------------------------------
# "blocked" is inadmissible in the read path
# ---------------------------------------------------------------------------


class TestBlockedIsInadmissible:
    def _build_and_seal_healthy(self, segment: Path) -> None:
        _write_manifest(segment, sources=["pi-agent-skills", "claude-skills"])
        _write_config(
            segment,
            required_sources=["pi-agent-skills", "claude-skills"],
        )
        _build(segment)

    def test_blocked_live_receipt_falls_back_to_last_valid(
        self, tmp_path: Path
    ) -> None:
        """Live receipt with blocked → inadmissible → loader falls back to last_valid."""
        segment = _make_segment(tmp_path)
        self._build_and_seal_healthy(segment)

        # Corrupt live receipt to declare blocked
        live_receipt = segment / "_ctx" / _RECEIPT
        _patch_receipt(live_receipt, publication_state="blocked")

        service = ContextService(segment)
        # Should not raise — falls back to last_valid which is healthy
        result = service.search("skill", k=5)

        assert result.authority_state == "healthy", (
            "After rejecting blocked live receipt, fallback to last_valid (healthy)"
        )

    def test_blocked_live_no_last_valid_raises_runtime_error(
        self, tmp_path: Path
    ) -> None:
        """Blocked live + no last_valid → RuntimeError (fails closed)."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment)
        _write_config(segment)
        _build(segment)

        # Remove last_valid so there's no fallback
        lv_dir = segment / "_ctx" / _LAST_VALID
        for p in lv_dir.iterdir():
            p.unlink()
        lv_dir.rmdir()

        # Patch live to blocked
        live_receipt = segment / "_ctx" / _RECEIPT
        _patch_receipt(live_receipt, publication_state="blocked")

        service = ContextService(segment)
        with pytest.raises(RuntimeError, match="No valid promoted set"):
            service.search("skill", k=5)

    def test_blocked_last_valid_with_healthy_live_still_serves_live(
        self, tmp_path: Path
    ) -> None:
        """If live is healthy and last_valid was somehow blocked, live is served normally."""
        segment = _make_segment(tmp_path)
        self._build_and_seal_healthy(segment)

        # Corrupt last_valid to blocked (fabrication)
        lv_receipt = segment / "_ctx" / _LAST_VALID / _RECEIPT
        _patch_receipt(lv_receipt, publication_state="blocked")

        service = ContextService(segment)
        # Live is healthy → served without touching last_valid
        result = service.search("skill", k=5)

        assert result.authority_state == "healthy"

    def test_blocked_both_live_and_last_valid_raises(self, tmp_path: Path) -> None:
        """Both live and last_valid blocked → RuntimeError."""
        segment = _make_segment(tmp_path)
        self._build_and_seal_healthy(segment)

        _patch_receipt(segment / "_ctx" / _RECEIPT, publication_state="blocked")
        _patch_receipt(
            segment / "_ctx" / _LAST_VALID / _RECEIPT, publication_state="blocked"
        )

        service = ContextService(segment)
        with pytest.raises(RuntimeError, match="No valid promoted set"):
            service.search("skill", k=5)

    def test_blocked_is_never_normalized_to_healthy(self, tmp_path: Path) -> None:
        """Confirm: blocked is never exposed as 'healthy' in authority_state."""
        segment = _make_segment(tmp_path)
        _write_manifest(segment)
        _write_config(segment)
        _build(segment)

        # Remove last_valid so blocked live has no escape
        lv_dir = segment / "_ctx" / _LAST_VALID
        for p in lv_dir.iterdir():
            p.unlink()
        lv_dir.rmdir()

        _patch_receipt(segment / "_ctx" / _RECEIPT, publication_state="blocked")

        service = ContextService(segment)
        with pytest.raises(RuntimeError):
            service.search("skill", k=5)

    def test_blocked_error_message_is_diagnostic(self, tmp_path: Path) -> None:
        """The error appended for 'blocked' must be diagnostic, not silent."""
        from src.application.context_service import ContextService as CS

        segment = _make_segment(tmp_path)
        _write_manifest(segment)
        _write_config(segment)
        _build(segment)

        lv_dir = segment / "_ctx" / _LAST_VALID
        for p in lv_dir.iterdir():
            p.unlink()
        lv_dir.rmdir()

        _patch_receipt(segment / "_ctx" / _RECEIPT, publication_state="blocked")

        with pytest.raises(RuntimeError) as exc_info:
            CS(segment).search("skill", k=5)

        # The RuntimeError message must reference inadmissible/blocked
        assert "inadmissible" in str(exc_info.value).lower() or "valid promoted" in str(
            exc_info.value
        ).lower()
