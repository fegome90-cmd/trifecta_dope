ctx_dir.mkdir()
    aliases = {
        "schema_version": 3,
        "features": {
            "telemetry_feature": {
                "priority": 4,
                "nl_triggers": ["telemetry"],
                "bundle": {"chunks": ["c1"], "paths": ["p1.py"]},
            }
        },
    }
    (ctx_dir / "aliases.yaml").write_text(json.dumps(aliases))
    (tmp_path / "p1.py").write_text("# p1")
    (ctx_dir / "prime_test.md").write_text("# Test\n## [INDEX]\n### index.entrypoints\n| Path | Razón |\n|------|-------|\n| `README.md` | Entry |")

    use_case = PlanUseCase(mock_filesystem, mock_telemetry)
    result = use_case.execute(tmp_path, "telemetry")
    assert result["selected_by"] == "fallback"
    assert result["l2_warning"] == "weak_single_word_trigger"
```
