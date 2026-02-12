from pathlib import Path


def test_pending_wos_exist():
    pending = list(Path("_ctx/jobs/pending").glob("WO-*.yaml"))
    assert pending, "Expected at least one pending WO"
    assert Path("_ctx/jobs/running").exists()
