from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = REPO_ROOT / "scripts" / "skill-hub"
CARDS = REPO_ROOT / "scripts" / "skill-hub-cards"


def build_wrapper_sandbox(tmp_path: Path) -> Path:
    root = tmp_path / "sandbox"
    root.mkdir()
    wrapper = root / "skill-hub"
    helper = root / "skill-hub-cards"
    shutil.copy2(WRAPPER, wrapper)
    helper.write_text(
        "#!/usr/bin/env python3\n"
        "from __future__ import annotations\n"
        "import os, sys\n"
        "sys.stdout.write(os.environ.get('MOCK_STDOUT', ''))\n"
        "sys.stderr.write(os.environ.get('MOCK_STDERR', ''))\n"
        "raise SystemExit(int(os.environ.get('MOCK_EXIT', '0')))\n"
    )
    helper.chmod(0o755)
    return wrapper


def run_wrapper(
    wrapper: Path,
    *,
    args: list[str],
    exit_code: int,
    stdout: str,
    stderr: str,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "MOCK_EXIT": str(exit_code),
            "MOCK_STDOUT": stdout,
            "MOCK_STDERR": stderr,
        }
    )
    return subprocess.run(
        ["bash", str(wrapper), *args],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def run_wrapper_cards(
    wrapper: Path,
    *,
    query: str,
    exit_code: int,
    stdout: str,
    stderr: str,
) -> subprocess.CompletedProcess[str]:
    return run_wrapper(
        wrapper,
        args=["--cards", query, "--limit", "1"],
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
    )


def build_cards_sandbox(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "cards-sandbox"
    root.mkdir()
    cards = root / "skill-hub-cards"
    shutil.copy2(CARDS, cards)

    uv = root / "uv"
    uv.write_text(
        "#!/usr/bin/env python3\n"
        "from __future__ import annotations\n"
        "import os, sys\n"
        "args = sys.argv[1:]\n"
        "if args[:4] == ['run', 'trifecta', 'ctx', 'search']:\n"
        "    sys.stdout.write(os.environ.get('MOCK_SEARCH_STDOUT', ''))\n"
        "    sys.stderr.write(os.environ.get('MOCK_SEARCH_STDERR', ''))\n"
        "    raise SystemExit(int(os.environ.get('MOCK_SEARCH_EXIT', '0')))\n"
        "if args[:4] == ['run', 'trifecta', 'ctx', 'get']:\n"
        "    sys.stdout.write(os.environ.get('MOCK_GET_STDOUT', ''))\n"
        "    sys.stderr.write(os.environ.get('MOCK_GET_STDERR', ''))\n"
        "    raise SystemExit(int(os.environ.get('MOCK_GET_EXIT', '0')))\n"
        "print('unexpected uv invocation: ' + ' '.join(args), file=sys.stderr)\n"
        "raise SystemExit(99)\n"
    )
    uv.chmod(0o755)
    return cards, root


def run_cards(
    cards: Path,
    *,
    args: list[str],
    stdin: str = "",
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        ["python3", str(cards), *args],
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
        env=merged_env,
    )


def test_wrapper_cards_mode_renders_intro_and_sentence_guidance_to_stdout(tmp_path: Path) -> None:
    wrapper = build_wrapper_sandbox(tmp_path)
    result = run_wrapper_cards(
        wrapper,
        query="find me a good testing skill",
        exit_code=0,
        stdout="# Skill: checkpoint-card\n",
        stderr="",
    )

    assert result.returncode == 0
    lowered = result.stdout.lower()
    assert "skill hub" in lowered
    assert "sentence" in lowered and "query" in lowered
    assert "# Skill: checkpoint-card\n" in result.stdout
    assert result.stderr == ""


def test_wrapper_cards_mode_keeps_governed_error_cards_on_stderr_and_preserves_exit_code(
    tmp_path: Path,
) -> None:
    wrapper = build_wrapper_sandbox(tmp_path)
    result = run_wrapper_cards(
        wrapper,
        query="metadata only request",
        exit_code=3,
        stdout="",
        stderr="TRIFECTA_ERROR_CODE: SKILL_HUB_METADATA_ONLY\n",
    )

    assert result.returncode == 3
    assert "TRIFECTA_ERROR_CODE" not in result.stdout
    assert "TRIFECTA_ERROR_CODE: SKILL_HUB_METADATA_ONLY" in result.stderr


def test_wrapper_cards_mode_fails_closed_for_runtime_failures(tmp_path: Path) -> None:
    wrapper = build_wrapper_sandbox(tmp_path)
    result = run_wrapper_cards(
        wrapper,
        query="broken runtime",
        exit_code=1,
        stdout="",
        stderr="TRIFECTA_ERROR_CODE: SKILL_HUB_RUNTIME_FAILURE\n",
    )

    assert result.returncode == 1
    assert "TRIFECTA_ERROR_CODE: SKILL_HUB_RUNTIME_FAILURE" in result.stderr


def test_wrapper_cards_mode_empty_query_fails_closed_with_governed_error_card(tmp_path: Path) -> None:
    wrapper = build_wrapper_sandbox(tmp_path)
    result = run_wrapper_cards(
        wrapper,
        query="",
        exit_code=0,
        stdout="# Skill: should-not-run\n",
        stderr="",
    )

    assert result.returncode == 1
    assert "TRIFECTA_ERROR_CODE: SKILL_HUB_EMPTY_QUERY" in result.stderr
    assert "# Skill: should-not-run" not in result.stdout


def test_wrapper_cards_mode_propagates_malformed_payload_diagnostics(tmp_path: Path) -> None:
    wrapper = build_wrapper_sandbox(tmp_path)
    result = run_wrapper_cards(
        wrapper,
        query="bad json",
        exit_code=1,
        stdout="",
        stderr="skill-hub-cards: parse error: invalid JSON search payload\n",
    )

    assert result.returncode == 1
    assert "parse error: invalid JSON search payload" in result.stderr


def test_skill_hub_cards_subprocess_renderable_path(tmp_path: Path) -> None:
    cards, sandbox_root = build_cards_sandbox(tmp_path)
    result = run_cards(
        cards,
        args=["find testing", "--limit", "1"],
        env={
            "PATH": f"{sandbox_root}:{os.environ.get('PATH', '')}",
            "MOCK_SEARCH_STDOUT": (
                '{"hits":[{"ref":"skill:go-testing:abc123","score":0.97}]}\n'
            ),
            "MOCK_GET_STDOUT": (
                "## [skill:go-testing:abc123] go-testing\n"
                "read /tmp/go-testing/SKILL.md\n"
                "**Source**: codex\n"
                "Use when writing go tests.\n"
            ),
        },
    )

    assert result.returncode == 0, result.stderr
    assert "# Skill: go-testing" in result.stdout
    assert "read /tmp/go-testing/SKILL.md" in result.stdout
    assert result.stderr == ""


def test_skill_hub_cards_subprocess_non_renderable_path(tmp_path: Path) -> None:
    cards, sandbox_root = build_cards_sandbox(tmp_path)
    result = run_cards(
        cards,
        args=["find metadata", "--limit", "1"],
        env={
            "PATH": f"{sandbox_root}:{os.environ.get('PATH', '')}",
            "MOCK_SEARCH_STDOUT": (
                '{"hits":[{"ref":"session:session_trifecta_dope:abc123","score":0.90}]}\n'
            ),
            "MOCK_GET_STDOUT": "## [session:session_trifecta_dope:abc123] session\nmetadata only\n",
        },
    )

    assert result.returncode == 3
    assert "# No valid skill cards" in result.stderr
    assert "# Skill:" not in result.stdout


def test_skill_hub_cards_subprocess_malformed_payload_path(tmp_path: Path) -> None:
    cards, _ = build_cards_sandbox(tmp_path)
    result = run_cards(
        cards,
        args=["--stdin-search-output"],
        stdin="{broken-json",
    )

    assert result.returncode == 1
    assert "parse error: invalid JSON search payload" in result.stderr


def test_skill_hub_cards_subprocess_empty_query_path(tmp_path: Path) -> None:
    cards, _ = build_cards_sandbox(tmp_path)
    result = run_cards(cards, args=[])

    assert result.returncode == 1
    assert "query required unless --stdin-search-output is provided" in result.stderr


def test_wrapper_runtime_contract_forbids_home_bin_authority_dependency() -> None:
    text = WRAPPER.read_text()

    assert ".local/bin" not in text
    assert "skill_hub_info_card.py" not in text


def test_wrapper_cards_mode_flag_is_order_independent(tmp_path: Path) -> None:
    wrapper = build_wrapper_sandbox(tmp_path)
    expected_stdout = "# Skill: go-testing\n"

    before = run_wrapper(
        wrapper,
        args=["--cards", "go testing", "--limit", "1"],
        exit_code=0,
        stdout=expected_stdout,
        stderr="",
    )
    after = run_wrapper(
        wrapper,
        args=["go testing", "--cards", "--limit", "1"],
        exit_code=0,
        stdout=expected_stdout,
        stderr="",
    )

    assert before.returncode == 0
    assert after.returncode == 0
    assert expected_stdout in before.stdout
    assert expected_stdout in after.stdout
    assert "skill hub" in before.stdout.lower()
    assert "skill hub" in after.stdout.lower()
    assert before.stderr == after.stderr == ""


def test_wrapper_default_path_emits_governed_intro_before_search_output(tmp_path: Path) -> None:
    wrapper = build_wrapper_sandbox(tmp_path)
    uv = tmp_path / "uv"
    uv.write_text(
        "#!/usr/bin/env python3\n"
        "from __future__ import annotations\n"
        "import os, sys\n"
        "args = sys.argv[1:]\n"
        "if args[:4] == ['run', 'trifecta', 'ctx', 'search']:\n"
        "    sys.stdout.write(os.environ.get('MOCK_SEARCH_STDOUT', ''))\n"
        "    raise SystemExit(0)\n"
        "print('unexpected uv invocation: ' + ' '.join(args), file=sys.stderr)\n"
        "raise SystemExit(99)\n"
    )
    uv.chmod(0o755)
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{tmp_path}:{env.get('PATH', '')}",
            "MOCK_SEARCH_STDOUT": "1. [repo:go-testing.md:abc] go-testing\n",
        }
    )
    result = subprocess.run(
        ["bash", str(wrapper), "find testing skills"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    lowered = result.stdout.lower()
    intro_index = lowered.find("=== skill hub ===")
    guidance_index = lowered.find("sentence query")
    results_index = lowered.find("1. [repo:go-testing.md:abc] go-testing")

    assert intro_index >= 0
    assert guidance_index >= 0
    assert results_index >= 0
    assert intro_index < results_index
    assert guidance_index < results_index
