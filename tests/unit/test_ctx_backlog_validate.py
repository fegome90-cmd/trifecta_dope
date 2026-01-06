import subprocess


def test_ctx_backlog_validate_ok():
    result = subprocess.run(
        ["python", "scripts/ctx_backlog_validate.py", "--fixtures"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
