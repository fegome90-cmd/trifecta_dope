from __future__ import annotations

import os
import json
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = REPO_ROOT / "scripts" / "skill-hub"


def build_wrapper_sandbox(tmp_path: Path) -> Path:
    root = tmp_path / "sandbox"
    root.mkdir()
    wrapper = root / "skill-hub"
    helper = root / "skill-hub-cards"
    shutil.copy2(WRAPPER, wrapper)
    helper.write_text(
        "#!/usr/bin/env python3\n"
        "from __future__ import annotations\n"
        "import json, os, sys\n"
        "arg_log = os.environ.get('MOCK_ARG_LOG')\n"
        "if arg_log:\n"
        "    with open(arg_log, 'w', encoding='utf-8') as fh:\n"
        "        json.dump(sys.argv[1:], fh)\n"
        "sys.stdout.write(os.environ.get('MOCK_STDOUT', ''))\n"
        "sys.stderr.write(os.environ.get('MOCK_STDERR', ''))\n"
        "raise SystemExit(int(os.environ.get('MOCK_EXIT', '0')))\n"
    )
    helper.chmod(0o755)
    return wrapper


def run_wrapper(wrapper: Path, *, query: str, exit_code: int, stdout: str, stderr: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({
        "MOCK_EXIT": str(exit_code),
        "MOCK_STDOUT": stdout,
        "MOCK_STDERR": stderr,
    })
    return subprocess.run(
        ["bash", str(wrapper), "--cards", query, "--limit", "1"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def test_wrapper_passes_resolved_segment_to_governed_helper(tmp_path: Path) -> None:
    wrapper = build_wrapper_sandbox(tmp_path)
    arg_log = tmp_path / "helper-args.json"
    segment = tmp_path / "custom-segment"
    segment.mkdir()

    env = os.environ.copy()
    env.update({
        "MOCK_EXIT": "0",
        "MOCK_STDOUT": "",
        "MOCK_STDERR": "",
        "MOCK_ARG_LOG": str(arg_log),
        "SKILL_HUB_SEGMENT": str(segment),
    })

    result = subprocess.run(
        ["bash", str(wrapper), "--cards", "checkpoint handoff", "--limit", "2"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0
    helper_args = json.loads(arg_log.read_text())
    assert "--segment" in helper_args
    assert helper_args[helper_args.index("--segment") + 1] == str(segment)


def test_wrapper_propagates_renderable_success_exit_and_streams(tmp_path: Path) -> None:
    wrapper = build_wrapper_sandbox(tmp_path)
    result = run_wrapper(wrapper, query="checkpoint handoff", exit_code=0, stdout="# Skill: checkpoint-card\n", stderr="")

    assert result.returncode == 0
    assert result.stdout == "# Skill: checkpoint-card\n"
    assert result.stderr == ""


def test_wrapper_propagates_non_renderable_exit_and_stderr(tmp_path: Path) -> None:
    wrapper = build_wrapper_sandbox(tmp_path)
    result = run_wrapper(wrapper, query="prime", exit_code=3, stdout="", stderr="# Administrative metadata only\n")

    assert result.returncode == 3
    assert result.stdout == ""
    assert result.stderr == "# Administrative metadata only\n"


def test_wrapper_propagates_empty_exit_and_message(tmp_path: Path) -> None:
    wrapper = build_wrapper_sandbox(tmp_path)
    result = run_wrapper(wrapper, query="empty", exit_code=4, stdout="", stderr="# No search hits found\n")

    assert result.returncode == 4
    assert result.stdout == ""
    assert result.stderr == "# No search hits found\n"


def test_wrapper_propagates_runtime_error_exit_and_both_streams(tmp_path: Path) -> None:
    wrapper = build_wrapper_sandbox(tmp_path)
    result = run_wrapper(
        wrapper,
        query="broken",
        exit_code=1,
        stdout="partial stdout\n",
        stderr="skill-hub-cards: parse error\n",
    )

    assert result.returncode == 1
    assert result.stdout == "partial stdout\n"
    assert result.stderr == "skill-hub-cards: parse error\n"
