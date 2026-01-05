from pathlib import Path


def test_backlog_yaml_exists():
    assert Path("_ctx/backlog/backlog.yaml").exists()
