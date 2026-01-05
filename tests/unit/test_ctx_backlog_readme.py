from pathlib import Path


def test_backlog_readme_exists():
    assert Path("docs/backlog/README.md").exists()
