import json
from pathlib import Path

from scripts.ctx_wo_finish import validate_scope_verdict, validate_session_evidence


def test_validate_session_evidence_fails_without_intent(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "_ctx").mkdir(parents=True)
    (root / "_ctx" / "session_trifecta_dope.md").write_text("[WO-0045] result: done\n", encoding="utf-8")

    result = validate_session_evidence("WO-0045", root)

    assert result.is_err()
    assert "intent" in result.unwrap_err()


def test_validate_session_evidence_fails_without_result(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "_ctx").mkdir(parents=True)
    (root / "_ctx" / "session_trifecta_dope.md").write_text("[WO-0045] intent: start\n", encoding="utf-8")

    result = validate_session_evidence("WO-0045", root)

    assert result.is_err()
    assert "result" in result.unwrap_err()


def test_validate_session_evidence_passes_with_both_markers(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "_ctx").mkdir(parents=True)
    (root / "_ctx" / "session_trifecta_dope.md").write_text(
        "[WO-0045] intent: start\n[WO-0045] result: pass\n",
        encoding="utf-8",
    )

    result = validate_session_evidence("WO-0045", root)

    assert result.is_ok()


def test_validate_scope_verdict_fails_if_missing(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "_ctx" / "logs" / "WO-0045").mkdir(parents=True)

    result = validate_scope_verdict("WO-0045", root)

    assert result.is_err()
    assert "Missing scope verification verdict" in result.unwrap_err()


def test_validate_scope_verdict_fails_if_not_pass(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    verdict_dir = root / "_ctx" / "logs" / "WO-0045"
    verdict_dir.mkdir(parents=True)
    (verdict_dir / "verdict.json").write_text(
        json.dumps({"wo_id": "WO-0045", "status": "FAIL"}),
        encoding="utf-8",
    )

    result = validate_scope_verdict("WO-0045", root)

    assert result.is_err()
    assert "not PASS" in result.unwrap_err()


def test_validate_scope_verdict_passes_with_pass_status(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    verdict_dir = root / "_ctx" / "logs" / "WO-0045"
    verdict_dir.mkdir(parents=True)
    (verdict_dir / "verdict.json").write_text(
        json.dumps({"wo_id": "WO-0045", "status": "PASS"}),
        encoding="utf-8",
    )

    result = validate_scope_verdict("WO-0045", root)

    assert result.is_ok()
