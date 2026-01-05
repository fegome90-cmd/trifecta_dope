y_telemetry": {
                "priority": 4,
                "nl_triggers": ["telemetry"],
                "support_terms": ["stats"],
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
    result = use_case.execute(tmp_path, "telemetry stats")

    assert result["l2_support_terms_required"] is True
    assert result["l2_support_terms_present"] == ["stats"]
    assert result["l2_weak_single_word_trigger"] is False
    assert result["l2_clamp_decision"] == "allow"
```
