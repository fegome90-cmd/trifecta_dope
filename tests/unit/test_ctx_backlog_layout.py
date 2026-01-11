from pathlib import Path


def test_backlog_layout():
    assert Path("_ctx/backlog").exists()
    legacy = Path("_ctx/blacklog")
    if legacy.exists():
        assert legacy.is_dir()
        assert (legacy / "README.md").exists()
        extra = {p.name for p in legacy.iterdir()} - {"README.md"}
        assert not extra
