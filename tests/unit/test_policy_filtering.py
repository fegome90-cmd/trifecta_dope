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
        ignored, blocked = filter_paths_by_policy(paths, policy)
        assert ignored == ["_ctx/session_trifecta.md", "_ctx/telemetry/events.jsonl"]
        assert blocked == []
        assert "src/main.py" not in ignored
        assert "tests/test_main.py" not in ignored

    def test_allowlist_contract_only(self):
        from scripts.ctx_wo_finish import filter_paths_by_policy

        policy = {"ignore": [], "allowlist_contract": ["_ctx/jobs/pending/**", "_ctx/backlog/**"]}
        paths = [
            "src/main.py",
            "_ctx/jobs/pending/WO-001.yaml",
            "_ctx/backlog/feature.md",
        ]
        ignored, blocked = filter_paths_by_policy(paths, policy)
        assert ignored == []
        assert blocked == ["_ctx/jobs/pending/WO-001.yaml", "_ctx/backlog/feature.md"]

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
        ignored, blocked = filter_paths_by_policy(paths, policy)
        assert ignored == ["_ctx/session_trifecta.md"]
        assert blocked == ["_ctx/jobs/pending/WO-001.yaml"]

    def test_priority_ignore_before_allowlist(self):
        from scripts.ctx_wo_finish import filter_paths_by_policy

        policy = {
            "ignore": ["_ctx/jobs/**"],
            "allowlist_contract": ["_ctx/jobs/pending/**"],
        }
        paths = ["_ctx/jobs/pending/WO-001.yaml"]
        ignored, blocked = filter_paths_by_policy(paths, policy)
        assert ignored == ["_ctx/jobs/pending/WO-001.yaml"]
        assert blocked == []

    def test_empty_policy(self):
        from scripts.ctx_wo_finish import filter_paths_by_policy

        policy = {"ignore": [], "allowlist_contract": []}
        paths = ["src/main.py", "_ctx/anything.yaml"]
        ignored, blocked = filter_paths_by_policy(paths, policy)
        assert ignored == []
        assert blocked == []

    def test_missing_keys(self):
        from scripts.ctx_wo_finish import filter_paths_by_policy

        policy = {}
        paths = ["src/main.py", "_ctx/anything.yaml"]
        ignored, blocked = filter_paths_by_policy(paths, policy)
        assert ignored == []
        assert blocked == []


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
