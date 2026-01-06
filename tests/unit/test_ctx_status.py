import subprocess


def test_ctx_status_help():
    result = subprocess.run(
        ["python", "scripts/ctx_status.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
