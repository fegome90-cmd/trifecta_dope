from pathlib import Path

import yaml


def test_ci_lint_job_enforces_wo_gates_and_telemetry_artifact() -> None:
    workflow_path = Path(".github/workflows/ci.yml")
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    lint_job = workflow["jobs"]["lint"]
    steps = lint_job["steps"]

    run_commands = [step.get("run", "") for step in steps]
    assert any("make wo-fmt-check" in cmd for cmd in run_commands)
    assert any("make wo-lint" in cmd for cmd in run_commands)
    assert any(
        "make wo-lint-json > _ctx/telemetry/wo_lint.json" in cmd
        for cmd in run_commands
    )

    artifact_steps = [
        step for step in steps if str(step.get("uses", "")).startswith("actions/upload-artifact@")
    ]
    assert artifact_steps, "Missing upload-artifact step for WO lint telemetry"
    artifact_path = str(artifact_steps[0]["with"]["path"])
    assert "_ctx/telemetry/wo_lint.json" in artifact_path
    assert "_ctx/telemetry/wo_debt.json" in artifact_path
