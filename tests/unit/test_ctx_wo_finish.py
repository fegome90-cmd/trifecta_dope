import subprocess


def test_wo_finish_help():
    result = subprocess.run(
        ["python", "scripts/ctx_wo_finish.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
