```python
def test_l2_specificity_beats_priority_for_multiword_trigger(mock_filesystem, mock_telemetry, tmp_path):
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    aliases = {
        "schema_version": 3,
        "features": {
            "telemetry_feature": {
                "priority": 4,
                "nl_triggers": ["telemetry"],
                "bundle": {"chunks": ["c1"], "paths": ["p1.py"]},
            },
            "symbol_surface": {
                "priority": 2,
                "nl_triggers": ["telemetry class"],
                "bundle": {"chunks": ["c2"], "paths": ["p2.py"]},
            },
        },
    }
    (ctx_dir / "aliases.yaml").write_text(json.dumps(aliases))
    (tmp_path / "p1.py").write_text("# p1")
    (tmp_path / "p2.py").write_text("# p2")
    (ctx_dir / "prime_test.md").write_text("# Test\n## [INDEX]\n### index.entrypoints\n| Path | Razón |\n|------|-------|\n| `README.md` | Entry |")

    use_case = PlanUseCase(mock_filesystem, mock_telemetry)
    result = use_case.execute(tmp_path, "how is the telemetry class constructed")
    assert result["selected_feature"] == "symbol_surface"
    assert result["selected_by"] == "nl_trigger"

def test_l2_single_word_clamp_blocks_without_support_terms(mock_filesystem, mock_telemetry, tmp_path):
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    aliases = {
        "schema_version": 3,
        "
