import json
from pathlib import Path

import pytest


def test_export_wo_index_atomicity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from scripts import export_wo_index

    repo_ctx = tmp_path
    index_dir = repo_ctx / "_ctx" / "index"
    index_dir.mkdir(parents=True, exist_ok=True)

    # Generate some dummy index to exist initially
    index_file = index_dir / "wo_worktrees.json"
    initial_content = {"version": "0.1"}
    index_file.write_text(json.dumps(initial_content))
    tmp_file = index_dir / "wo_worktrees.json.tmp"

    monkeypatch.setattr(export_wo_index, "get_repo_root", lambda: repo_ctx)
    monkeypatch.setattr(export_wo_index, "get_git_head_sha", lambda _root: "deadbeef")
    monkeypatch.setattr(export_wo_index, "get_worktrees_from_git", lambda _root: {})

    original_replace = Path.replace

    def crashing_replace(self: Path, target: Path | str) -> Path:
        if self == tmp_file and Path(target) == index_file:
            raise RuntimeError("CRASH ATOMIC REPLACE")
        return original_replace(self, target)

    monkeypatch.setattr(Path, "replace", crashing_replace)

    with pytest.raises(RuntimeError, match="CRASH ATOMIC REPLACE"):
        export_wo_index.main()

    # VERIFY ATOMICITY INVARIANTS
    # 1. The original index must remain untouched
    current_content = json.loads(index_file.read_text())
    assert current_content == initial_content, "Original index was corrupted or overwritten"

    # 2. The fixed temp artifact used by export_wo_index.py must not survive the crash.
    tmp_files = list(index_dir.glob("wo_worktrees.json.tmp*"))
    assert index_file.exists()
    assert not tmp_files
