import os
from pathlib import Path
import pytest
from src.domain.segment_resolver import get_repo_root

@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Fixture to provide the repository root path."""
    return get_repo_root()

@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture to isolate HOME environment during tests."""
    home_dir = tmp_path / "fake_home"
    home_dir.mkdir()
    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.setenv("USERPROFILE", str(home_dir)) # Windows support
    return home_dir
