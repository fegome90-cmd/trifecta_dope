import subprocess


def test_wo_take_help():
    result = subprocess.run(
        ["python", "scripts/ctx_wo_take.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
