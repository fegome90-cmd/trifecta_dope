import pytest
import json
from pathlib import Path
import re


def test_prime_top10_in_pack():
    """Tripwire: Top 10 paths in Prime MUST be in context_pack.json."""

    # 1. Parse Prime for Top 10 Paths
    prime_path = Path("_ctx/prime_trifecta_dope.md")
    if not prime_path.exists():
        pytest.skip("Prime file missing")

    lines = prime_path.read_text().splitlines()
    target_paths = []

    for line in lines:
        line = line.strip()
        # Strict match: "N. `path`"
        m = re.match(r"^\d+\.\s+`([^`]+)`$", line)
        if m:
            target_paths.append(m.group(1))
            if len(target_paths) >= 10:
                break

    assert len(target_paths) >= 9, f"Prime should have at least 9 items, found: {len(target_paths)}"

    # 2. Check Pack
    pack_path = Path("_ctx/context_pack.json")
    if not pack_path.exists():
        pytest.fail("context_pack.json missing. Run 'ctx sync' first.")

    data = json.loads(pack_path.read_text())
    # In pack, paths might be stored relative to segment root?
    # Prime paths are "trifecta_dope/src/..."
    # If segment root is "trifecta_dope", then pack path might be "src/..."
    # OR if pack was built with segment=".", and path was "trifecta_dope/src/...",
    # BuildContextPackUseCase: SourceFile(path=str(file_path.relative_to(target_path.parent))...)
    # target_path.parent is 'agent_h'.
    # So "trifecta_dope/src/..." is correct relative path.

    pack_paths = set(s["path"] for s in data.get("source_files", []))

    missing = []
    for tp in target_paths:
        if tp not in pack_paths:
            missing.append(tp)

    assert not missing, (
        f"Missing paths in context_pack.json: {missing}. \nPack contains ({len(pack_paths)}): {sorted(list(pack_paths))}"
    )
