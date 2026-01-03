import re
from pathlib import Path
import pytest
import json


def test_prime_is_paths_only():
    """Tripwire: Prime must contain paths to real files, not text chunks."""
    prime_path = Path("_ctx/prime_trifecta_dope.md")
    if not prime_path.exists():
        # Fallback for dynamic environments: find any prime_*.md
        prime_files = list(Path("_ctx").glob("prime_*.md"))
        if not prime_files:
            pytest.skip("No prime file found for audit")
        prime_path = prime_files[0]

    content = prime_path.read_text()

    # Regex to find numbered list items: "1. `path` ..."
    # We enforce backticks for paths as per strict convention
    # or at least that the item resolves to a file

    lines = content.splitlines()
    found_paths = 0

    for line in lines:
        line = line.strip()
        # Look for "N. `path`" or "N. path"
        match = re.match(r"^\d+\.\s+`?([^`\s]+)`?", line)
        if match:
            path_str = match.group(1)
            # Remove parentheses comments if any inside the backticks (rare)
            # or if the regex captured too much.
            # The previous edit used: 1. `path` (Comment)

            # Re-eval regex for: 1. `path` (Comment)
            # path is in backticks.
            backtick_match = re.search(r"`([^`]+)`", line)
            if backtick_match:
                path_str = backtick_match.group(1)

            # Assertions
            # 1. Length sanity (no chunks)
            assert len(line) < 200, f"Line too long, suspected chunk: {line[:50]}..."

            # 2. File existence
            # Paths in Prime should be relative to repo root (trifecta_dope/...) or relative to segment?
            # The file says: "**REPO_ROOT**: `/Users/felipe_gonzalez/Developer/agent_h`"
            # And paths are "trifecta_dope/src/..."

            # We need to check existence.
            # We are running in trifecta_dope root.
            # If path starts with trifecta_dope/, we need to resolve it relative to parent of cwd?
            # OR relative to whatever logic BuildContextPackUseCase uses.

            # Let's try to resolve absolute path assuming CWD is trifecta_dope
            # If path is `trifecta_dope/src/...`, then:
            #   Repo Root = ../
            #   Path = ../trifecta_dope/src/...  (which is ./src/...)

            repo_root = Path("..").resolve()
            candidate = repo_root / path_str

            if not candidate.exists():
                # Try relative to cwd (if user put src/... directly)
                candidate_local = Path(path_str)
                if not candidate_local.exists():
                    pytest.fail(
                        f"Prime path mismatch: {path_str} does not exist via RepoRoot ({candidate}) or CWD ({candidate_local})"
                    )

            assert candidate.is_file(), f"Path must be a file: {path_str}"
            found_paths += 1

    assert found_paths >= 5, "Prime must list at least 5 priority files"


def test_prime_topN_in_pack_after_sync(tmp_path):
    """Tripwire: Top paths in Prime MUST end up in context_pack.json source_files."""
    # 1. Setup a clean segment in tmp_path
    # Copy necessary files to simulate a segment
    import shutil

    # We need the real _ctx/prime_trifecta_dope.md to test IT specifically
    # But we want to run 'ctx sync' safely.
    # Actually, we can just inspect the CURRENT context_pack.json if we trust it was synced.
    # If the user wants us to EXECUTE ctx sync, we should do it here or assume previous step did it.
    # The requirement says: "ejecuta ctx sync en un tmp workspace"

    # Copy source code subset to tmp_path to allow build
    dest = tmp_path / "trifecta_dope"
    dest.mkdir()

    # We define a minimal segment with the REAL prime file
    ctx_dir = dest / "_ctx"
    ctx_dir.mkdir()

    real_prime = Path("_ctx/prime_trifecta_dope.md")
    if not real_prime.exists():
        pytest.skip("Prime file missing")

    shutil.copy(real_prime, ctx_dir / real_prime.name)

    # We need a dummy skill/agent to pass validation
    (dest / "skill.md").write_text("# Skill\n")
    (ctx_dir / "agent_trifecta_dope.md").write_text("# Agent\n")

    # Create the files referenced in Prime (dummy content) so they exist
    prime_content = real_prime.read_text()
    paths = []
    for line in prime_content.splitlines():
        m = re.search(r"`([^`]+)`", line)
        if m and line.strip()[0].isdigit():
            p = m.group(1)
            paths.append(p)

            # Create file
            # p is likely "trifecta_dope/src/..."
            # We are inside "dest" (which represents trifecta_dope dir)
            # If p starts with trifecta_dope/, strip it
            if p.startswith("trifecta_dope/"):
                rel = p.replace("trifecta_dope/", "", 1)
            else:
                rel = p

            f = dest / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("Dummy content for build test")

    # Run `ctx sync` inside dest
    # We call the CLI module directly
    from typer.testing import CliRunner

    _runner = CliRunner()

    # We need to mock sys.path or ensure imports work?
    # We will use subprocess instead to be closer to real execution, but we need the project code available.
    # `uv run` works.

    # Actually, we can just use the UseCase directly to avoid environment complexity of subprocess in tmp
    # But imports might be tricky if we move files.

    # Let's simply Verify the LIVE context_pack.json in the real repo,
    # assuming the previous step synced it.
    # OR run the UseCase on the temp dir.

    # Let's try running the UseCase programmatically on tmp_path
    from src.application.use_cases import SyncContextUseCase
    from src.infrastructure.file_system import FileSystemAdapter

    fs = FileSystemAdapter()
    uc = SyncContextUseCase(fs, telemetry=None)

    # We need to fix the "repo_root" resolution in BuildContextPackUseCase
    # It tries to find files.
    # We faked them in `dest`.

    # Execute (targeting the directory)
    result = uc.execute(dest)
    assert "synced and validated" in result or "Validation Passed" in result or "✅" in result

    # Verify Pack
    pack_path = ctx_dir / "context_pack.json"
    assert pack_path.exists()

    data = json.loads(pack_path.read_text())
    source_paths = [s["path"] for s in data.get("source_files", [])]

    # Assert top paths are present
    for p in paths[:5]:  # Check top 5
        # logic in creation:
        # path is relative to segment root?
        # SourceFile(path=str(file_path.relative_to(target_path.parent))...)
        # If target_path is "dest" (trifecta_dope), parent is tmp_path.
        # file_path was "dest/src/..."
        # relative to parent -> "trifecta_dope/src/..."

        # We assume the pack stores them as "trifecta_dope/src/..."
        # p coming from Prime is "trifecta_dope/src/..."

        assert p in source_paths, f"Critical file {p} missing from context pack after sync"
