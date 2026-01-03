"""Unit tests for telemetry PII sanitization."""

from src.infrastructure.telemetry import _sanitize_value, _sanitize_event


class TestSanitizeValue:
    """Test _sanitize_value function for PII path redaction."""

    def test_posix_users_path_redacted(self):
        assert _sanitize_value("/Users/alice/project") == "<ABS_PATH_REDACTED>"

    def test_posix_home_path_redacted(self):
        assert _sanitize_value("/home/bob/repo") == "<ABS_PATH_REDACTED>"

    def test_posix_private_var_redacted(self):
        assert (
            _sanitize_value("/private/var/folders/k1/jz_hmygd3k36/T/pytest-107/test")
            == "<ABS_PATH_REDACTED>"
        )

    def test_wsl_path_redacted(self):
        assert _sanitize_value("/mnt/c/Users/charlie/code") == "<ABS_PATH_REDACTED>"
        assert _sanitize_value("/mnt/C/Users/dave/proj") == "<ABS_PATH_REDACTED>"

    def test_windows_c_users_redacted(self):
        assert _sanitize_value("C:\\Users\\eve\\project") == "<ABS_PATH_REDACTED>"

    def test_windows_d_users_redacted(self):
        assert _sanitize_value("D:\\users\\frank\\code") == "<ABS_PATH_REDACTED>"

    def test_file_uri_redacted(self):
        assert _sanitize_value("file:///Users/grace/file.py") == "<ABS_URI_REDACTED>"
        assert _sanitize_value("file:///home/henry/doc.md") == "<ABS_URI_REDACTED>"

    def test_relative_path_unchanged(self):
        assert _sanitize_value("relative/path/file.py") == "relative/path/file.py"

    def test_dot_path_unchanged(self):
        assert _sanitize_value(".") == "."

    def test_current_dir_unchanged(self):
        assert _sanitize_value("./src/main.py") == "./src/main.py"

    def test_parent_dir_unchanged(self):
        assert _sanitize_value("../utils/helper.py") == "../utils/helper.py"


class TestSanitizeEvent:
    """Test _sanitize_event function for event dict sanitization."""

    def test_sanitizes_args_segment_posix(self):
        event = {
            "cmd": "ctx.build",
            "args": {"segment": "/Users/ida/project"},
            "result": {"status": "ok"},
        }
        result = _sanitize_event(event)
        assert result["args"]["segment"] == "<ABS_PATH_REDACTED>"

    def test_sanitizes_args_segment_windows(self):
        event = {
            "cmd": "ctx.sync",
            "args": {"segment": "C:\\Users\\jack\\repo"},
            "result": {"status": "ok"},
        }
        result = _sanitize_event(event)
        assert result["args"]["segment"] == "<ABS_PATH_REDACTED>"

    def test_preserves_relative_segment(self):
        event = {"cmd": "ctx.get", "args": {"segment": "."}, "result": {"chunks": 2}}
        result = _sanitize_event(event)
        assert result["args"]["segment"] == "."

    def test_preserves_other_args(self):
        event = {
            "cmd": "ctx.search",
            "args": {"segment": "/Users/kim/proj", "query": "test"},
            "result": {"hits": 5},
        }
        result = _sanitize_event(event)
        assert result["args"]["query"] == "test"  # Other args unchanged
        assert result["args"]["segment"] == "<ABS_PATH_REDACTED>"

    def test_handles_missing_args(self):
        event = {"cmd": "status", "result": {"ok": True}}
        result = _sanitize_event(event)
        assert result == event  # No error, returns as-is

    def test_handles_missing_segment_in_args(self):
        event = {"cmd": "version", "args": {"verbose": True}, "result": {"version": "1.0"}}
        result = _sanitize_event(event)
        assert result["args"]["verbose"] is True  # Unchanged

    def test_env_var_allow_bypasses_sanitization(self, monkeypatch):
        """Test TRIFECTA_PII=allow preserves absolute paths."""
        monkeypatch.setenv("TRIFECTA_PII", "allow")

        event = {
            "cmd": "ctx.build",
            "args": {"segment": "/Users/leo/secret"},
            "result": {"status": "ok"},
        }
        result = _sanitize_event(event)
        assert result["args"]["segment"] == "/Users/leo/secret"  # NOT redacted

    def test_env_var_other_value_does_not_bypass(self, monkeypatch):
        """Test TRIFECTA_PII=deny (or any other value) still sanitizes."""
        monkeypatch.setenv("TRIFECTA_PII", "deny")

        event = {
            "cmd": "ctx.sync",
            "args": {"segment": "/home/mary/code"},
            "result": {"status": "ok"},
        }
        result = _sanitize_event(event)
        assert result["args"]["segment"] == "<ABS_PATH_REDACTED>"

    def test_sanitizes_args_cwd(self):
        """Test that args.cwd is sanitized."""
        event = {
            "cmd": "exec",
            "args": {"cwd": "/Users/nancy/workspace"},
            "result": {"status": "ok"},
        }
        result = _sanitize_event(event)
        assert result["args"]["cwd"] == "<ABS_PATH_REDACTED>"

    def test_sanitizes_args_path(self):
        """Test that args.path is sanitized."""
        event = {
            "cmd": "file.read",
            "args": {"path": "/home/oscar/data.json"},
            "result": {"bytes": 1024},
        }
        result = _sanitize_event(event)
        assert result["args"]["path"] == "<ABS_PATH_REDACTED>"

    def test_sanitizes_args_root(self):
        """Test that args.root is sanitized."""
        event = {
            "cmd": "init",
            "args": {"root": "/private/var/folders/tmp/project"},
            "result": {"status": "ok"},
        }
        result = _sanitize_event(event)
        assert result["args"]["root"] == "<ABS_PATH_REDACTED>"

    def test_sanitizes_args_file(self):
        """Test that args.file is sanitized."""
        event = {
            "cmd": "parse",
            "args": {"file": "C:\\Users\\paul\\script.py"},
            "result": {"ok": True},
        }
        result = _sanitize_event(event)
        assert result["args"]["file"] == "<ABS_PATH_REDACTED>"

    def test_sanitizes_args_uri(self):
        """Test that args.uri is sanitized."""
        event = {
            "cmd": "open",
            "args": {"uri": "file:///Users/quinn/doc.md"},
            "result": {"opened": True},
        }
        result = _sanitize_event(event)
        assert result["args"]["uri"] == "<ABS_URI_REDACTED>"

    def test_handles_non_string_values_safely(self):
        """Test that non-string values don't crash sanitization."""
        event = {
            "cmd": "compute",
            "args": {
                "segment": ".",  # string, will be unchanged
                "count": 42,  # int, should NOT be sanitized
                "enabled": True,  # bool, should NOT be sanitized
                "items": ["a", "b"],  # list, should NOT be sanitized
            },
            "result": {"ok": True},
        }
        result = _sanitize_event(event)
        assert result["args"]["segment"] == "."
        assert result["args"]["count"] == 42
        assert result["args"]["enabled"] is True
        assert result["args"]["items"] == ["a", "b"]
