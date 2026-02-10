from pathlib import Path


def test_pending_wos_exist():
    assert Path("_ctx/jobs/pending/WO-0004.yaml").exists()
    assert Path("_ctx/jobs/running/WO-0005.yaml").exists()
