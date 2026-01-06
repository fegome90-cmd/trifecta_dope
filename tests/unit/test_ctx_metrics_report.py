import subprocess


def test_ctx_metrics_help():
    result = subprocess.run(
        ["python", "scripts/ctx_metrics_report.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
