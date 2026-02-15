import yaml


class TestPathMatchesPatterns:
    """Tests for path_matches_patterns function."""

    def test_exact_match(self):
        from scripts.ctx_wo_finish import path_matches_patterns

        assert path_matches_patterns("src/main.py", ["src/main.py"]) is True
        assert path_matches_patterns("src/other.py", ["src/main.py"]) is False

    def test_glob_star_single(self):
        from scripts.ctx_wo_finish import path_matches_patterns

        assert path_matches_patterns("src/main.py", ["src/*.py"]) is True
        assert path_matches_patterns("src/main/main.py", ["src/*.py"]) is False

    def test_glob_star_double(self):
        from scripts.ctx_wo_finish import path_matches_patterns

        assert path_matches_patterns("src/main.py", ["src/**/*.py"]) is True
        assert path_matches_patterns("src/main/main.py", ["src/**/*.py"]) is True
        assert path_matches_patterns("other/main.py", ["src/**/*.py"]) is False

    def test_glob_question(self):
        from scripts.ctx_wo_finish import path_matches_patterns

        assert path_matches_patterns("file1.py", ["file?.py"]) is True
        assert path_matches_patterns("file10.py", ["file?.py"]) is False

    def test_multiple_patterns(self):
        from scripts.ctx_wo_finish import path_matches_patterns

        patterns = ["src/*.py", "tests/*.py", "docs/*.md"]
        assert path_matches_patterns("src/main.py", patterns) is True
        assert path_matches_patterns("tests/test_main.py", patterns) is True
        assert path_matches_patterns("other/file.py", patterns) is False

    def test_empty_patterns(self):
        from scripts.ctx_wo_finish import path_matches_patterns

        assert path_matches_patterns("any/path", []) is False


class TestFilterPathsByPolicy:
    """Tests for filter_paths_by_policy function."""

    def test_ignore_only(self):
        from scripts.ctx_wo_finish import filter_paths_by_policy

        policy = {"ignore": ["_ctx/session_*.md", "_ctx/telemetry/**"], "allowlist_contract": []}
        paths = [
            "src/main.py",
            "_ctx/session_trifecta.md",
            "_ctx/telemetry/events.jsonl",
            "tests/test_main.py",
        ]
        ignored, blocked, unknown = filter_paths_by_policy(paths, policy)
        assert ignored == ["_ctx/session_trifecta.md", "_ctx/telemetry/events.jsonl"]
        assert blocked == []
        assert unknown == ["src/main.py", "tests/test_main.py"]
        assert "src/main.py" not in ignored

    def test_allowlist_contract_only(self):
        from scripts.ctx_wo_finish import filter_paths_by_policy

        policy = {"ignore": [], "allowlist_contract": ["_ctx/jobs/pending/**", "_ctx/backlog/**"]}
        paths = [
            "src/main.py",
            "_ctx/jobs/pending/WO-001.yaml",
            "_ctx/backlog/feature.md",
        ]
        ignored, blocked, unknown = filter_paths_by_policy(paths, policy)
        assert ignored == []
        assert blocked == ["_ctx/jobs/pending/WO-001.yaml", "_ctx/backlog/feature.md"]
        assert unknown == ["src/main.py"]

    def test_both_ignore_and_allowlist(self):
        from scripts.ctx_wo_finish import filter_paths_by_policy

        policy = {
            "ignore": ["_ctx/session_*.md"],
            "allowlist_contract": ["_ctx/jobs/pending/**"],
        }
        paths = [
            "src/main.py",
            "_ctx/session_trifecta.md",
            "_ctx/jobs/pending/WO-001.yaml",
        ]
        ignored, blocked, unknown = filter_paths_by_policy(paths, policy)
        assert ignored == ["_ctx/session_trifecta.md"]
        assert blocked == ["_ctx/jobs/pending/WO-001.yaml"]
        assert unknown == ["src/main.py"]

    def test_priority_ignore_before_allowlist(self):
        from scripts.ctx_wo_finish import filter_paths_by_policy

        policy = {
            "ignore": ["_ctx/jobs/**"],
            "allowlist_contract": ["_ctx/jobs/pending/**"],
        }
        paths = ["_ctx/jobs/pending/WO-001.yaml"]
        ignored, blocked, unknown = filter_paths_by_policy(paths, policy)
        assert ignored == ["_ctx/jobs/pending/WO-001.yaml"]
        assert blocked == []
        assert unknown == []

    def test_empty_policy(self):
        from scripts.ctx_wo_finish import filter_paths_by_policy

        policy = {"ignore": [], "allowlist_contract": []}
        paths = ["src/main.py", "_ctx/anything.yaml"]
        ignored, blocked, unknown = filter_paths_by_policy(paths, policy)
        assert ignored == []
        assert blocked == []
        assert unknown == ["src/main.py", "_ctx/anything.yaml"]

    def test_missing_keys(self):
        from scripts.ctx_wo_finish import filter_paths_by_policy

        policy = {}
        paths = ["src/main.py", "_ctx/anything.yaml"]
        ignored, blocked, unknown = filter_paths_by_policy(paths, policy)
        assert ignored == []
        assert blocked == []
        assert unknown == ["src/main.py", "_ctx/anything.yaml"]

    def test_unknown_path_blocks(self):
        from scripts.ctx_wo_finish import filter_paths_by_policy

        policy = {"ignore": ["_ctx/session_*.md"], "allowlist_contract": ["_ctx/jobs/pending/**"]}
        paths = ["_ctx/new_file.yaml"]
        ignored, blocked, unknown = filter_paths_by_policy(paths, policy)
        assert ignored == []
        assert blocked == []
        assert unknown == ["_ctx/new_file.yaml"]

    def test_unknown_with_ignored_and_blocked(self):
        from scripts.ctx_wo_finish import filter_paths_by_policy

        policy = {
            "ignore": ["_ctx/session_*.md"],
            "allowlist_contract": ["_ctx/jobs/pending/**"],
        }
        paths = [
            "_ctx/session_trifecta.md",  # ignored
            "_ctx/jobs/pending/WO-001.yaml",  # blocked
            "_ctx/new_file.yaml",  # unknown - should be caught!
        ]
        ignored, blocked, unknown = filter_paths_by_policy(paths, policy)
        assert ignored == ["_ctx/session_trifecta.md"]
        assert blocked == ["_ctx/jobs/pending/WO-001.yaml"]
        assert unknown == ["_ctx/new_file.yaml"]

    def test_non_ctx_paths_always_allowed(self):
        from scripts.ctx_wo_finish import filter_paths_by_policy

        policy = {"ignore": [], "allowlist_contract": []}
        paths = [
            "src/main.py",  # non-ctx - should be unknown
            "tests/test.py",  # non-ctx - should be unknown
            "_ctx/config.yaml",  # ctx but not in policy - should be unknown
        ]
        ignored, blocked, unknown = filter_paths_by_policy(paths, policy)
        assert ignored == []
        assert blocked == []
        assert unknown == paths  # All are unknown


class TestLoadFinishPolicy:
    """Tests for load_finish_policy function."""

    def test_loads_existing_policy(self, tmp_path):
        from scripts.ctx_wo_finish import load_finish_policy

        policy_file = tmp_path / "_ctx" / "policy" / "ctx_finish_ignore.yaml"
        policy_file.parent.mkdir(parents=True)
        policy_file.write_text(
            yaml.dump(
                {
                    "ignore": ["_ctx/session_*.md"],
                    "allowlist_contract": ["_ctx/jobs/pending/**"],
                }
            )
        )

        result = load_finish_policy(tmp_path)
        assert result["ignore"] == ["_ctx/session_*.md"]
        assert result["allowlist_contract"] == ["_ctx/jobs/pending/**"]

    def test_returns_empty_on_missing_file(self, tmp_path):
        from scripts.ctx_wo_finish import load_finish_policy

        result = load_finish_policy(tmp_path)
        assert result == {"ignore": [], "allowlist_contract": []}

    def test_returns_empty_on_missing_policy_dir(self, tmp_path):
        from scripts.ctx_wo_finish import load_finish_policy

        result = load_finish_policy(tmp_path)
        assert result == {"ignore": [], "allowlist_contract": []}
