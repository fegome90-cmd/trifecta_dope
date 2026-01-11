```python
def test_l2_single_word_requires_support_terms(mock_filesystem, mock_telemetry, tmp_path):
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    aliases = {
        "schema_version": 3,
        "features": {
            "observability_telemetry": {
                "priority": 4,
                "nl_triggers": ["telemetry"],
                "support_terms": ["stats", "metrics"],
                "bundle": {"chunks": ["c1"], "paths": ["p1.py"]},
            }
        },
    }
    (ctx_dir / "aliases.yaml").write_text(json.dumps(aliases))
    (tmp_path / "p1.py").write_text("# p1")
    (ctx_dir / "prime_test.md").write_text(
        "# Test\n## [INDEX]\n### index.entrypoints\n| Path | Razn |\n|------|-------|\n| `README.md` | Entry |"
    )

    use_case = PlanUseCase(mock_filesystem, mock_telemetry)
    blocked = use_case.execute(tmp_path, "telemetry")
    allowed = use_case.execute(tmp_path, "telemetry stats")

    assert blocked["selected_by"] == "fallback"
    assert blocked["l2_warning"] == "weak_single_word_trigger"
    assert allowed["selected_by"] == "nl_trigger"


def test_l2_support_terms_telemetry_fields(mock_filesystem, mock_telemetry, tmp_path):
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    aliases = {
        "schema_version": 3,
        "features": {
            "observability_telemetry": {
                "priority": 4,
                "nl_tri
