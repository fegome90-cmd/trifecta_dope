from pathlib import Path


def test_linear_modules_do_not_reference_wo_mutation_scripts() -> None:
    files = sorted(Path("src/application").glob("linear_*.py")) + [Path("src/infrastructure/linear_mcp_client.py")]
    joined = "\n".join(p.read_text(encoding="utf-8") for p in files if p.exists())

    assert "ctx_wo_take" not in joined
    assert "ctx_wo_finish" not in joined


def test_linear_modules_do_not_write_jobs_yaml_paths() -> None:
    files = sorted(Path("src/application").glob("linear_*.py")) + [Path("src/infrastructure/linear_mcp_client.py")]

    for path in files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # Outbound viewer may read _ctx/jobs, but must not mutate those files.
        forbidden_patterns = [
            "_ctx/jobs" + "\".write_text(",
            "_ctx/jobs" + "\".open(\"w\"",
            "_ctx/jobs" + "\".open('w'",
        ]
        normalized = text.replace(" ", "")
        for pattern in forbidden_patterns:
            assert pattern.replace(" ", "") not in normalized, f"Forbidden jobs write pattern in {path}"
