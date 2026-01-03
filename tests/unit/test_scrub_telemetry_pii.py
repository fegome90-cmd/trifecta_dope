"""Unit tests for scrub_telemetry_pii script."""

from pathlib import Path
import sys

# Add scripts to path for import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scrub_telemetry_pii import scrub_line, scrub_file


class TestScrubLine:
    """Test scrub_line function."""

    def test_redacts_posix_users_path(self):
        line = '{"args": {"segment": "/Users/alice/project"}}\n'
        scrubbed, modified = scrub_line(line)
        assert '"segment": "<ABS_PATH_REDACTED>"' in scrubbed
        assert modified is True

    def test_redacts_home_path(self):
        line = '{"args": {"path": "/home/bob/file.txt"}}\n'
        scrubbed, modified = scrub_line(line)
        assert "<ABS_PATH_REDACTED>" in scrubbed
        assert modified is True

    def test_redacts_private_var(self):
        line = '{"args": {"cwd": "/private/var/folders/tmp/test"}}\n'
        scrubbed, modified = scrub_line(line)
        assert "<ABS_PATH_REDACTED>" in scrubbed
        assert modified is True

    def test_redacts_file_uri(self):
        line = '{"args": {"uri": "file:///Users/charlie/doc.md"}}\n'
        scrubbed, modified = scrub_line(line)
        assert "<ABS_URI_REDACTED>" in scrubbed
        assert modified is True

    def test_unchanged_for_relative_paths(self):
        line = '{"args": {"segment": "./relative/path"}}\n'
        scrubbed, modified = scrub_line(line)
        assert scrubbed == line
        assert modified is False


class TestScrubFile:
    """Test scrub_file function."""

    def test_scrubs_file_and_creates_backup(self, tmp_path):
        # Create test events.jsonl with PII
        events_file = tmp_path / "events.jsonl"
        events_file.write_text(
            '{"cmd": "ctx.build", "args": {"segment": "/Users/test/project"}}\n'
            '{"cmd": "ctx.sync", "args": {"segment": "."}}\n'
        )

        result = scrub_file(events_file)

        # Check return value
        assert result["lines_scanned"] == 2
        assert result["lines_modified"] == 1
        assert Path(result["backup_path"]).exists()

        # Check scrubbed content
        scrubbed_content = events_file.read_text()
        assert "<ABS_PATH_REDACTED>" in scrubbed_content
        assert '"/Users/' not in scrubbed_content

        # Check backup
        backup_content = Path(result["backup_path"]).read_text()
        assert "/Users/test/project" in backup_content
