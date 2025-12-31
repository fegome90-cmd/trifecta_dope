from __future__ import annotations

from pathlib import Path


def parse_feature_map(prime_path: Path) -> dict[str, list[str]]:
    """Parse PRIME index.feature_map table into feature -> paths mapping.

    Args:
        prime_path: Path to PRIME markdown file

    Returns:
        Dictionary mapping feature names to lists of file paths

    Raises:
        ValueError: If feature_map table is malformed
    """
    content = prime_path.read_text()
    lines = content.splitlines()
    feature_map: dict[str, list[str]] = {}

    in_table = False
    found_header = False

    for line in lines:
        if line.strip().startswith("### index.feature_map"):
            in_table = True
            continue
        if in_table and line.strip().startswith("### "):
            break

        if not in_table or not line.strip().startswith("|"):
            continue

        cols = [c.strip() for c in line.strip("|").split("|")]

        # Skip separator row (contains only dashes and pipes)
        if len(cols) >= 1 and all(c == "" or all(ch == "-" for ch in c) for c in cols):
            continue

        # Header row starts with "Feature"
        if len(cols) >= 1 and cols[0] == "Feature":
            found_header = True
            continue

        # Data row: must have at least 3 columns (feature, chunk_ids, paths)
        if found_header and len(cols) >= 3 and cols[0]:
            feature = cols[0]
            paths_raw = cols[2]
            paths = [p.strip().strip("`") for p in paths_raw.split(",") if p.strip()]
            feature_map[feature] = paths

    if in_table and not found_header:
        raise ValueError("Malformed feature_map table: header row not found")

    return feature_map


def evaluate_pcc(
    expected_feature: str,
    predicted_feature: str | None,
    predicted_paths: list[str],
    feature_map: dict[str, list[str]],
    selected_by: str,
) -> dict[str, bool]:
    expected_paths = feature_map.get(expected_feature, []) if expected_feature != "fallback" else []
    path_correct = bool(
        expected_feature != "fallback"
        and predicted_feature == expected_feature
        and any(p in expected_paths for p in predicted_paths)
    )

    false_fallback = expected_feature != "fallback" and selected_by == "fallback"
    safe_fallback = expected_feature == "fallback" and selected_by == "fallback"

    return {
        "path_correct": path_correct,
        "false_fallback": false_fallback,
        "safe_fallback": safe_fallback,
    }


def summarize_pcc(rows: list[dict[str, bool]]) -> dict[str, int]:
    return {
        "path_correct_count": sum(1 for r in rows if r.get("path_correct")),
        "false_fallback_count": sum(1 for r in rows if r.get("false_fallback")),
        "safe_fallback_count": sum(1 for r in rows if r.get("safe_fallback")),
    }
