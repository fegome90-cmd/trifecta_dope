import shutil
import subprocess
from pathlib import Path


def _init_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    return root


def _install_hook_script(repo_root: Path) -> None:
    source = Path(__file__).resolve().parents[2] / "scripts" / "prevent_manual_wo_closure.sh"
    target = repo_root / "scripts" / "prevent_manual_wo_closure.sh"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(source, target)
    target.chmod(0o755)


def _run_hook(repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "scripts/prevent_manual_wo_closure.sh"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def _commit_all(repo_root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo_root, check=True)


def test_hook_blocks_done_add_without_evidence_bundle(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _install_hook_script(repo)
    _commit_all(repo, "seed hook")
    (repo / "_ctx/jobs/done").mkdir(parents=True)
    (repo / "_ctx/jobs/done/WO-7777.yaml").write_text(
        "id: WO-7777\nstatus: done\nverified_at_sha: abc\nclosed_at: now\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "_ctx/jobs/done/WO-7777.yaml"], cwd=repo, check=True)

    result = _run_hook(repo)

    assert result.returncode == 1
    assert "added without deleting _ctx/jobs/running/WO-7777.yaml" in (result.stdout + result.stderr)


def test_hook_blocks_when_closure_scripts_change_same_commit(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _install_hook_script(repo)
    _commit_all(repo, "seed hook")
    (repo / "_ctx/jobs/running").mkdir(parents=True)
    (repo / "_ctx/jobs/done").mkdir(parents=True)
    (repo / "_ctx/handoff/WO-8888").mkdir(parents=True)

    running = repo / "_ctx/jobs/running/WO-8888.yaml"
    done = repo / "_ctx/jobs/done/WO-8888.yaml"
    verdict = repo / "_ctx/handoff/WO-8888/verdict.json"
    report = repo / "_ctx/handoff/WO-8888/verification_report.log"

    running.write_text("id: WO-8888\nstatus: running\n", encoding="utf-8")
    subprocess.run(["git", "add", str(running.relative_to(repo))], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "seed running"], cwd=repo, check=True)

    running.unlink()
    done.write_text(
        "id: WO-8888\nstatus: done\nverified_at_sha: abc\nclosed_at: now\n",
        encoding="utf-8",
    )
    verdict.write_text("{}", encoding="utf-8")
    report.write_text("ok", encoding="utf-8")

    script_path = repo / "scripts/ctx_wo_finish.py"
    script_path.write_text("# touched\n", encoding="utf-8")

    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    result = _run_hook(repo)

    assert result.returncode == 1
    assert "Cannot close WO while mutating closure scripts" in (result.stdout + result.stderr)


def test_hook_allows_valid_closure_bundle(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _install_hook_script(repo)
    _commit_all(repo, "seed hook")
    (repo / "_ctx/jobs/running").mkdir(parents=True)
    (repo / "_ctx/jobs/done").mkdir(parents=True)
    (repo / "_ctx/handoff/WO-9999").mkdir(parents=True)

    running = repo / "_ctx/jobs/running/WO-9999.yaml"
    done = repo / "_ctx/jobs/done/WO-9999.yaml"
    verdict = repo / "_ctx/handoff/WO-9999/verdict.json"
    report = repo / "_ctx/handoff/WO-9999/verification_report.log"

    running.write_text("id: WO-9999\nstatus: running\n", encoding="utf-8")
    subprocess.run(["git", "add", str(running.relative_to(repo))], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "seed running"], cwd=repo, check=True)

    running.unlink()
    done.write_text(
        "id: WO-9999\nstatus: done\nverified_at_sha: abc\nclosed_at: now\n",
        encoding="utf-8",
    )
    verdict.write_text("{}", encoding="utf-8")
    report.write_text("ok", encoding="utf-8")

    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    result = _run_hook(repo)

    assert result.returncode == 0, (result.stdout + result.stderr)
