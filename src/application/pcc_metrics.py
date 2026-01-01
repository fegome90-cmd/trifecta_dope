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

        # Skip separator row (non-empty columns contain only dashes)
        if len(cols) >= 1 and all(c == "" or (c and all(ch == "-" for ch in c)) for c in cols):
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
    """Evaluate PCC metrics for a single prediction against an expected feature.

    The function compares an expected feature and its associated paths from
    ``feature_map`` with a predicted feature and predicted paths, and computes
    simple boolean metrics that can be aggregated by :func:`summarize_pcc`.

    Args:
        expected_feature: The ground-truth feature name. The special value
            ``"fallback"`` indicates that no specific feature was expected.
        predicted_feature: The feature selected by the model or system, or
            ``None`` if no feature was predicted.
        predicted_paths: List of file paths associated with the prediction.
        feature_map: Mapping from feature name to the list of canonical file
            paths for that feature, as returned by :func:`parse_feature_map`.
        selected_by: A string indicating which selector chose the prediction,
            e.g. ``"fallback"`` when the fallback mechanism was used.

    Returns:
        A dictionary with the following boolean keys:

        * ``"path_correct"``: ``True`` if a non-fallback expected feature was
          correctly predicted and at least one predicted path matches a path
          for the expected feature.
        * ``"false_fallback"``: ``True`` if a specific feature was expected
          but the prediction was selected by the fallback mechanism.
        * ``"safe_fallback"``: ``True`` if no specific feature was expected
          (``expected_feature == "fallback"``) and the fallback mechanism was
          used.
    """
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
    """Aggregate PCC evaluation metrics across multiple task results.

    Args:
        rows: A list of dictionaries, typically produced by :func:`evaluate_pcc`,
            where each dictionary contains boolean flags for "path_correct",
            "false_fallback", and "safe_fallback".

    Returns:
        A dictionary with integer counts summarizing the input rows:

        - "path_correct_count": Number of rows with ``path_correct`` set to True.
        - "false_fallback_count": Number of rows with ``false_fallback`` set to True.
        - "safe_fallback_count": Number of rows with ``safe_fallback`` set to True.
    """
    return {
        "path_correct_count": sum(1 for r in rows if r.get("path_correct")),
        "false_fallback_count": sum(1 for r in rows if r.get("false_fallback")),
        "safe_fallback_count": sum(1 for r in rows if r.get("safe_fallback")),
    }
