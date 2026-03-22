from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_install_trifecta_context_exits_with_deprecation_message(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "scripts" / "install_trifecta_context.py"
    segment = tmp_path / "demo-segment"
    ctx = segment / "_ctx"
    ctx.mkdir(parents=True)
    (segment / "skill.md").write_text("# skill\n", encoding="utf-8")
    (ctx / "agent_demo-segment.md").write_text("# agent\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(script), "--segment", str(segment)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    combined = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 1
    assert "DEPRECATED" in combined
    assert "install_FP.py" in combined
    assert "_ctx/agent.md" not in combined
