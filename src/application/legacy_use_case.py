"""Use Case for scanning legacy tech debt."""

import json
from pathlib import Path
from src.domain.result import Ok, Err


def scan_legacy(repo_root: Path, manifest_path: Path) -> "Ok[list[str]] | Err[list[str]]":
    """
    Scan repo for undeclared legacy patterns.
    Contract Legacy Patterns:
    1. _ctx/agent.md (no suffix)
    2. _ctx/prime.md (no suffix)
    3. _ctx/session.md (no suffix)
    4. scripts/ingest_trifecta.py

    Returns:
       Ok(found_legacy_paths) if all found items are in manifest.
       Err(undeclared_paths) if found items are NOT in manifest.
    """
    if not manifest_path.exists():
        # Fail-closed if manifest missing? Or empty?
        # Contract says "source unique", so should exist.
        return Err([f"Legacy manifest missing at {manifest_path}"])

    try:
        manifest_data = json.loads(manifest_path.read_text())
        declared_paths = {item["path"] for item in manifest_data}
    except Exception:
        return Err(["Legacy manifest is invalid JSON"])

    found_legacy = []
    undeclared = []

    # 1. Scan for Context Legacy files globally
    # Naive scan: walk repo.
    # Better: glob

    # Pattern A: _ctx/agent.md, prime.md, session.md
    for p in repo_root.glob("**/_ctx/*.md"):
        name = p.name
        if name in ["agent.md", "prime.md", "session.md", "job.md", "product.md"]:
            rel_path = str(p.relative_to(repo_root))
            found_legacy.append(rel_path)
            if rel_path not in declared_paths:
                undeclared.append(rel_path)

    # Pattern B: explicit scripts
    script = repo_root / "scripts/ingest_trifecta.py"
    if script.exists():
        rel = "scripts/ingest_trifecta.py"
        found_legacy.append(rel)
        if rel not in declared_paths:
            undeclared.append(rel)

    if undeclared:
        return Err([f"Undeclared legacy found: {p}" for p in undeclared])

    return Ok(found_legacy)
