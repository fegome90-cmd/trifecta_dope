nt", 100)
        telemetry.incr("ast_cache_hit_count", 86)
        telemetry.incr("ast_cache_miss_count", 14)

        telemetry.flush()

        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())

        assert last_run["ast"]["ast_parse_count"] == 100
        assert last_run["ast"]["ast_cache_hit_count"] == 86
        assert last_run["ast"]["ast_cache_miss_count"] == 14
        assert abs(last_run["ast"]["ast_cache_hit_rate"] - 0.86) < 0.01

    def test_lsp_summary(self, tmp_path):
        """Verify LSP summary calculation."""
        telemetry = Telemetry(tmp_path, level="lite")

        telemetry.incr("lsp_spawn_count", 5)
        telemetry.incr("lsp_ready_count", 5)
        telemetry.incr("lsp_fallback_count", 1)

        telemetry.flush()

        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())

        assert last_run["lsp"]["lsp_spawn_count"] == 5
        assert last_run["lsp"]["lsp_ready_count"] == 5
        assert last_run["lsp"]["lsp_ready_rate"] == 1.0
        assert abs(last_run["lsp"]["lsp_fallback_rate"] - 0.2) < 0.01

    def test_file_read_summary(self, tmp_path):
        """Verify file read summary calculation."""
        telemetry = Telemetry(tmp_path, level="lite")

        telemetry.incr("file_read_skeleton_by
