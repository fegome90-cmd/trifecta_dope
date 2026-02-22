import pytest
import os
import shutil
import tarfile
from pathlib import Path
from scripts.helpers import check_lock_age, check_lock_validity


def test_lock_ttl_default_semantic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    lock_file = tmp_path / "WO-0001.lock"
    lock_file.touch()

    # Default TTL is 86400.
    # Current time = N
    # mock stat to return N - 3600 (1 hour old)
    import time

    current_time = time.time()

    class MockStat:
        st_mtime = current_time - 3600

    monkeypatch.setattr(Path, "stat", lambda self, **kwargs: MockStat())
    # 1 hour is not stale
    assert check_lock_age(lock_file) is False

    # Mock stat to return N - 90000 (25 hours old)
    class MockStatStale:
        st_mtime = current_time - 90000

    monkeypatch.setattr(Path, "stat", lambda self, **kwargs: MockStatStale())
    # 25 hours is stale compared to default 24h
    assert check_lock_age(lock_file) is True


def test_lock_ttl_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    lock_file = tmp_path / "WO-0002.lock"
    lock_file.touch()

    # Override TTL to 3600 (1 hour)
    monkeypatch.setenv("WO_LOCK_TTL_SEC", "3600")

    import time

    current_time = time.time()

    # 2 hours old
    class MockStat:
        st_mtime = current_time - 7200

    monkeypatch.setattr(Path, "stat", lambda self, **kwargs: MockStat())

    # 2 hours is stale when TTL is 1 hour
    assert check_lock_age(lock_file) is True


def test_lock_ttl_env_invalid_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    lock_file = tmp_path / "WO-0003.lock"
    lock_file.touch()

    # Invalid TTL -> should fallback to 86400
    monkeypatch.setenv("WO_LOCK_TTL_SEC", "invalid_string_not_an_int")

    import time

    current_time = time.time()

    # 25 hours old (86400 is not enough)
    class MockStat:
        st_mtime = current_time - 90000

    monkeypatch.setattr(Path, "stat", lambda self, **kwargs: MockStat())
    assert check_lock_age(lock_file) is True
