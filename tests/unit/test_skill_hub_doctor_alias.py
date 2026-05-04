from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = REPO_ROOT / "scripts" / "skill-hub"


def _build_wrapper_sandbox(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname = 'fake-trifecta'\n")
    (root / "src").mkdir()

    wrapper = scripts / "skill-hub"
    shutil.copy2(WRAPPER, wrapper)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    uv = fake_bin / "uv"
    uv.write_text(
        "#!/usr/bin/env python3\n"
        "from __future__ import annotations\n"
        "import json, sys\n"
        "args = sys.argv[1:]\n"
        "query = ''\n"
        "limit = '5'\n"
        "for i, arg in enumerate(args):\n"
        "    if arg == '--query' and i + 1 < len(args):\n"
        "        query = args[i + 1]\n"
        "    if arg == '--limit' and i + 1 < len(args):\n"
        "        limit = args[i + 1]\n"
        "if '--explain' in args:\n"
        "    print(json.dumps({'expansions': {'expanded_terms': []}, 'hits': []}))\n"
        "    raise SystemExit(0)\n"
        "if query == 'skill-hub-doctor':\n"
        "    print('Search Results (1 hits):')\n"
        "    print('')\n"
        "    print('1. [skill:skill-hub-doctor:abc] skill-hub-doctor.md')\n"
        "    print('   Score: 10.00 | Tokens: ~100')\n"
        "    raise SystemExit(0)\n"
        "print(f'Search Results ({limit} hits):')\n"
        "print('')\n"
        "print('1. [skill:other:abc] other.md')\n"
        "print('   Score: 5.00 | Tokens: ~100')\n"
        "raise SystemExit(0)\n"
    )
    uv.chmod(0o755)
    return wrapper, fake_bin


def _run_wrapper(wrapper: Path, fake_bin: Path, query: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({
        "PATH": f"{fake_bin}:{env['PATH']}",
        "SKILL_HUB_TRIFECTA_ROOT": str(wrapper.parents[1]),
        "SKILL_HUB_SEGMENT": str(wrapper.parents[1] / "segment"),
    })
    return subprocess.run(
        ["bash", str(wrapper), query, "--limit", "5"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def test_doctor_weak_phrases_force_canonical_doctor_alias(tmp_path: Path) -> None:
    wrapper, fake_bin = _build_wrapper_sandbox(tmp_path)

    for query in ("exit code drift", "no me aparecen skills", "hub de skills"):
        run = _run_wrapper(wrapper, fake_bin, query)

        assert run.returncode == 0, run.stderr
        assert "Canonical alias match: skill-hub-doctor" in run.stdout
        assert "1. [skill:skill-hub-doctor:" in run.stdout
        assert f"Additional results for: {query}" in run.stdout


def test_unrelated_query_does_not_force_doctor_alias(tmp_path: Path) -> None:
    wrapper, fake_bin = _build_wrapper_sandbox(tmp_path)

    run = _run_wrapper(wrapper, fake_bin, "python testing")

    assert run.returncode == 0, run.stderr
    assert "Canonical alias match: skill-hub-doctor" not in run.stdout
