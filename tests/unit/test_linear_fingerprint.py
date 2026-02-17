from src.application.linear_fingerprint import compute_projection_fingerprint


def test_projection_fingerprint_is_stable_for_key_order() -> None:
    payload_a = {
        "title": "[WO-0001] Test",
        "description": "desc",
        "labels": ["trifecta", "status:pending"],
        "state": "st-1",
    }
    payload_b = {
        "state": "st-1",
        "labels": ["trifecta", "status:pending"],
        "description": "desc",
        "title": "[WO-0001] Test",
    }

    fp_a = compute_projection_fingerprint(payload_a, "v1")
    fp_b = compute_projection_fingerprint(payload_b, "v1")

    assert fp_a == fp_b


def test_projection_fingerprint_changes_with_policy_version() -> None:
    payload = {"title": "[WO-0001] Test"}
    fp_a = compute_projection_fingerprint(payload, "v1")
    fp_b = compute_projection_fingerprint(payload, "v2")
    assert fp_a != fp_b
