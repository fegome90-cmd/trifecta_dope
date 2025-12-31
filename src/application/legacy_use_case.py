"""Use Case for scanning legacy tech debt."""

import json
from pathlib import Path, PurePosixPath
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
        return Err([f"Legacy manifest missing at {manifest_path}"])

    try:
        manifest_data = json.loads(manifest_path.read_text())
        declared_patterns = {item["path"] for item in manifest_data}
    except Exception:
        return Err(["Legacy manifest is invalid JSON"])

    found_legacy = []
    undeclared = []

    # 1. Scan for Context Legacy files globally
    # SORTED GLOB for Input Determinism
    # Pattern A: _ctx/agent.md, prime.md, session.md
    # We use sorted() to ensure deterministic processing order
    for p in sorted(repo_root.glob("**/_ctx/*.md")):
        name = p.name
        # Removed job.md and product.md from scope as per "Clean Scope" rule
        if name in ["agent.md", "prime.md", "session.md"]:
            rel_path = str(p.relative_to(repo_root))
            found_legacy.append(rel_path)

            # Check against declared patterns (glob support)
            # Use PurePosixPath for consistent glob matching across OS
            is_declared = any(
                PurePosixPath(rel_path).match(pattern) for pattern in declared_patterns
            )

            if not is_declared:
                undeclared.append(rel_path)

    # Pattern B: explicit scripts
    script = repo_root / "scripts/ingest_trifecta.py"
    if script.exists():
        rel = "scripts/ingest_trifecta.py"
        found_legacy.append(rel)
        is_declared_script = any(PurePosixPath(rel).match(pattern) for pattern in declared_patterns)
        if not is_declared_script:
            undeclared.append(rel)

    if undeclared:
        # Sort errors for Output Determinism
        sorted_errors = sorted([f"Undeclared legacy found: {p}" for p in undeclared])
        return Err(sorted_errors)

    return Ok(sorted(found_legacy))
