"""Tests for alias merge logic between manual and generated aliases.

TDD RED phase - these tests define the expected behavior for merging
manual aliases.yaml with generated aliases.generated.yaml.
"""

from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]

from src.infrastructure.aliases_fs import (
    AliasMerger,
    GeneratedAliasWriter,
    load_aliases_yaml,
    merge_aliases,
    save_generated_aliases,
)


class TestLoadAliasesYaml:
    """Tests for loading aliases from YAML files."""

    def test_load_valid_yaml(self, tmp_path: Path) -> None:
        """Should load a valid aliases.yaml file."""
        aliases_file = tmp_path / "aliases.yaml"
        aliases_file.write_text(
            yaml.dump({"schema_version": 1, "aliases": {"test": ["skill1", "skill2"]}})
        )

        result = load_aliases_yaml(aliases_file)

        assert result == {"test": ["skill1", "skill2"]}

    def test_load_missing_file_returns_empty(self, tmp_path: Path) -> None:
        """Missing file should return empty dict."""
        result = load_aliases_yaml(tmp_path / "nonexistent.yaml")
        assert result == {}

    def test_load_invalid_schema_version_returns_empty(self, tmp_path: Path) -> None:
        """Invalid schema_version should return empty dict."""
        aliases_file = tmp_path / "aliases.yaml"
        aliases_file.write_text(yaml.dump({"schema_version": 99, "aliases": {}}))

        result = load_aliases_yaml(aliases_file)

        assert result == {}

    def test_load_missing_aliases_key_returns_empty(self, tmp_path: Path) -> None:
        """Missing aliases key should return empty dict."""
        aliases_file = tmp_path / "aliases.yaml"
        aliases_file.write_text(yaml.dump({"schema_version": 1}))

        result = load_aliases_yaml(aliases_file)

        assert result == {}

    def test_load_invalid_yaml_returns_empty(self, tmp_path: Path) -> None:
        """Invalid YAML should return empty dict."""
        aliases_file = tmp_path / "aliases.yaml"
        aliases_file.write_text(":::invalid:::yaml:::")

        result = load_aliases_yaml(aliases_file)

        assert result == {}

    def test_load_normalizes_keys_to_lowercase(self, tmp_path: Path) -> None:
        """Keys should be normalized to lowercase."""
        aliases_file = tmp_path / "aliases.yaml"
        aliases_file.write_text(
            yaml.dump({"schema_version": 1, "aliases": {"TEST": ["skill1"]}})
        )

        result = load_aliases_yaml(aliases_file)

        assert "test" in result
        assert "TEST" not in result


class TestMergeAliases:
    """Tests for alias merge logic."""

    def test_manual_takes_precedence(self) -> None:
        """Manual aliases should take precedence over generated."""
        manual = {"test": ["manual_skill"]}
        generated = {"test": ["generated_skill"]}

        result = merge_aliases(manual, generated)

        assert result["test"] == ["manual_skill"]

    def test_generated_adds_new_aliases(self) -> None:
        """Generated should add aliases not in manual."""
        manual = {"existing": ["skill1"]}
        generated = {"new": ["skill2"]}

        result = merge_aliases(manual, generated)

        assert "existing" in result
        assert "new" in result
        assert result["existing"] == ["skill1"]
        assert result["new"] == ["skill2"]

    def test_generated_does_not_modify_manual_lists(self) -> None:
        """Generated should not modify existing manual lists."""
        manual = {"test": ["skill1"]}
        generated = {"test": ["skill2", "skill3"]}

        result = merge_aliases(manual, generated)

        assert result["test"] == ["skill1"]
        assert len(result["test"]) == 1

    def test_both_empty_returns_empty(self) -> None:
        """Both empty should return empty dict."""
        result = merge_aliases({}, {})
        assert result == {}

    def test_manual_only(self) -> None:
        """Manual only should be returned."""
        manual = {"test": ["skill1"]}
        result = merge_aliases(manual, {})
        assert result == manual

    def test_generated_only(self) -> None:
        """Generated only should be returned."""
        generated = {"test": ["skill1"]}
        result = merge_aliases({}, generated)
        assert result == generated

    def test_deterministic_merge(self) -> None:
        """Merge should be deterministic (same input -> same output)."""
        manual = {"a": ["skill1"], "b": ["skill2"]}
        generated = {"b": ["skill3"], "c": ["skill4"]}

        result1 = merge_aliases(manual, generated)
        result2 = merge_aliases(manual, generated)

        assert result1 == result2


class TestAliasMerger:
    """Tests for AliasMerger class."""

    @pytest.fixture
    def merger(self, tmp_path: Path) -> AliasMerger:
        """Create an AliasMerger for testing."""
        return AliasMerger(segment_path=tmp_path)

    def test_load_manual_aliases(self, merger: AliasMerger, tmp_path: Path) -> None:
        """Should load manual aliases from _ctx/aliases.yaml."""
        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / "aliases.yaml").write_text(
            yaml.dump({"schema_version": 1, "aliases": {"manual": ["skill1"]}})
        )

        manual = merger.load_manual()

        assert manual == {"manual": ["skill1"]}

    def test_load_generated_aliases(
        self, merger: AliasMerger, tmp_path: Path
    ) -> None:
        """Should load generated aliases from _ctx/aliases.generated.yaml."""
        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / "aliases.generated.yaml").write_text(
            yaml.dump({"schema_version": 1, "aliases": {"generated": ["skill2"]}})
        )

        generated = merger.load_generated()

        assert generated == {"generated": ["skill2"]}

    def test_merge_returns_combined(
        self, merger: AliasMerger, tmp_path: Path
    ) -> None:
        """Merge should return combined aliases with manual precedence."""
        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / "aliases.yaml").write_text(
            yaml.dump({"schema_version": 1, "aliases": {"manual": ["skill1"]}})
        )
        (ctx_dir / "aliases.generated.yaml").write_text(
            yaml.dump({"schema_version": 1, "aliases": {"generated": ["skill2"]}})
        )

        merged = merger.merge()

        assert "manual" in merged
        assert "generated" in merged


class TestSaveGeneratedAliases:
    """Tests for saving generated aliases."""

    def test_save_creates_file(self, tmp_path: Path) -> None:
        """Should create aliases.generated.yaml file."""
        output_path = tmp_path / "aliases.generated.yaml"
        aliases = {"test": ["skill1", "skill2"]}

        save_generated_aliases(output_path, aliases)

        assert output_path.exists()

    def test_save_correct_schema_version(self, tmp_path: Path) -> None:
        """Saved file should have schema_version: 1."""
        output_path = tmp_path / "aliases.generated.yaml"
        aliases = {"test": ["skill1"]}

        save_generated_aliases(output_path, aliases)

        data = yaml.safe_load(output_path.read_text())
        assert data["schema_version"] == 1

    def test_save_correct_aliases(self, tmp_path: Path) -> None:
        """Saved file should contain correct aliases."""
        output_path = tmp_path / "aliases.generated.yaml"
        aliases = {"testing": ["pytest-skill", "unittest-skill"]}

        save_generated_aliases(output_path, aliases)

        data = yaml.safe_load(output_path.read_text())
        assert data["aliases"] == aliases

    def test_save_creates_parent_directory(self, tmp_path: Path) -> None:
        """Should create parent directory if it doesn't exist."""
        output_path = tmp_path / "subdir" / "aliases.generated.yaml"
        aliases = {"test": ["skill1"]}

        save_generated_aliases(output_path, aliases)

        assert output_path.exists()

    def test_save_overwrites_existing(self, tmp_path: Path) -> None:
        """Should overwrite existing file."""
        output_path = tmp_path / "aliases.generated.yaml"
        output_path.write_text(yaml.dump({"schema_version": 1, "aliases": {"old": ["x"]}}))

        new_aliases = {"new": ["skill1"]}
        save_generated_aliases(output_path, new_aliases)

        data = yaml.safe_load(output_path.read_text())
        assert "new" in data["aliases"]
        assert "old" not in data["aliases"]


class TestGeneratedAliasWriter:
    """Tests for GeneratedAliasWriter class."""

    @pytest.fixture
    def writer(self, tmp_path: Path) -> GeneratedAliasWriter:
        """Create a GeneratedAliasWriter for testing."""
        return GeneratedAliasWriter(segment_path=tmp_path)

    def test_write_creates_file(self, writer: GeneratedAliasWriter) -> None:
        """Should write aliases.generated.yaml."""
        aliases = {"test": ["skill1"]}

        output_path = writer.write(aliases)

        assert output_path.exists()

    def test_write_returns_output_path(
        self, writer: GeneratedAliasWriter, tmp_path: Path
    ) -> None:
        """Should return the output path."""
        aliases = {"test": ["skill1"]}

        output_path = writer.write(aliases)

        assert output_path == tmp_path / "_ctx" / "aliases.generated.yaml"

    def test_write_custom_output_path(self, tmp_path: Path) -> None:
        """Should respect custom output path."""
        custom_path = tmp_path / "custom.yaml"
        writer = GeneratedAliasWriter(segment_path=tmp_path, output_path=custom_path)
        aliases = {"test": ["skill1"]}

        result = writer.write(aliases)

        assert result == custom_path
        assert custom_path.exists()

    def test_dry_run_does_not_write(
        self, writer: GeneratedAliasWriter, tmp_path: Path
    ) -> None:
        """Dry run should not write file."""
        writer_dry = GeneratedAliasWriter(segment_path=tmp_path, dry_run=True)
        aliases = {"test": ["skill1"]}

        output_path = writer_dry.write(aliases)

        assert not output_path.exists()

    def test_dry_run_returns_expected_path(
        self, writer: GeneratedAliasWriter, tmp_path: Path
    ) -> None:
        """Dry run should still return expected path."""
        writer_dry = GeneratedAliasWriter(segment_path=tmp_path, dry_run=True)
        aliases = {"test": ["skill1"]}

        output_path = writer_dry.write(aliases)

        assert output_path == tmp_path / "_ctx" / "aliases.generated.yaml"
