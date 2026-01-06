import subprocess


def test_verify_run_help():
    result = subprocess.run(
        ["bash", "scripts/ctx_verify_run.sh", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
