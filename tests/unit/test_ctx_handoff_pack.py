import subprocess


def test_handoff_pack_help():
    result = subprocess.run(
        ["bash", "scripts/ctx_handoff_pack.sh", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
