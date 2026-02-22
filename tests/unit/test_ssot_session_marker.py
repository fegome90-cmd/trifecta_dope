import pytest
from pathlib import Path
from scripts.helpers import format_session_marker
from scripts.ctx_wo_finish import validate_session_evidence


def test_format_session_marker():
    wo_id = "WO-1234"
    assert format_session_marker(wo_id, "intent:") == "[WO-1234] intent:"
    assert format_session_marker(wo_id, "result:") == "[WO-1234] result:"


def test_format_session_marker_validation():
    """Test that format_session_marker validates inputs."""
    # Valid WO IDs should work
    assert format_session_marker("WO-0001", "intent:") == "[WO-0001] intent:"

    # Invalid WO IDs should raise ValueError
    with pytest.raises(ValueError, match="Invalid WO ID"):
        format_session_marker("wo-1234", "intent:")  # lowercase

    with pytest.raises(ValueError, match="Invalid WO ID"):
        format_session_marker("WO1234", "intent:")  # missing dash

    with pytest.raises(ValueError, match="Invalid WO ID"):
        format_session_marker("WO-123", "intent:")  # only 3 digits

    with pytest.raises(ValueError, match="Invalid WO ID"):
        format_session_marker("", "intent:")  # empty

    # Empty marker should raise ValueError
    with pytest.raises(ValueError, match="Marker cannot be empty"):
        format_session_marker("WO-1234", "")


def test_validate_session_evidence_exact_match(tmp_path: Path):
    wo_id = "WO-1234"
    root = tmp_path
    session_dir = root / "_ctx"
    session_dir.mkdir(parents=True)
    session_path = session_dir / "session_trifecta_dope.md"

    # 1. Missing markers -> Err
    session_path.write_text("Hello world")
    result = validate_session_evidence(wo_id, root)
    assert result.is_err()

    # 2. Invalid markers (variation in brackets/case) -> Err
    session_path.write_text(f"[wo-1234] intent:\n(WO-1234) result:")
    result = validate_session_evidence(wo_id, root)
    assert result.is_err()

    # 3. Exact valid markers via SSOT -> Ok
    intent = format_session_marker(wo_id, "intent: taking wo")
    res = format_session_marker(wo_id, "result: finished")

    session_path.write_text(f"doing work\n{intent}\nsome logs\n{res}\n")

    result = validate_session_evidence(wo_id, root)
    assert result.is_ok()
