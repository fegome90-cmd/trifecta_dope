"""Integration test: Context pack indexes custom high-value directories.

This test verifies the fix for WO-0009 and examen_grado case where
skills/, apps/, config/ directories were not being indexed.

GitHub Issue: Skills and custom directories missing from context pack
"""

import pytest
from pathlib import Path
from src.application.use_cases import BuildContextPackUseCase
from src.infrastructure.file_system import FileSystemAdapter


@pytest.fixture
def temp_segment(tmp_path):
    """Create a temporary segment with custom directory structure."""
    # Use fixed segment_id "test" to avoid derivation issues
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text("# Docs\n\nDocumentation content.")

    # Create custom high-value directories
    (tmp_path / "skills").mkdir()
    (tmp_path / "skills" / "test-skill").mkdir()
    (tmp_path / "skills" / "test-skill" / "SKILL.md").write_text(
        "---\nname: test-skill\n---\n# Test Skill\n\nThis is a test skill."
    )

    (tmp_path / "apps").mkdir()
    (tmp_path / "apps" / "test-app").mkdir()
    (tmp_path / "apps" / "test-app" / "main.py").write_text(
        "# Entry point\n\ndef main():\n    print('Hello')\n"
    )

    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "settings.yaml").write_text("app:\n  name: test\n  version: 1.0\n")

    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("def test_dummy():\n    assert True\n")

    # Create minimal Trifecta structure with fixed segment_id "test"
    (tmp_path / "_ctx").mkdir()
    (tmp_path / "skill.md").write_text("---\nname: test\n---\n# Test Segment\n")
    (tmp_path / "_ctx" / "agent_test.md").write_text("---\nsegment: test\n---\n# Agent\n")
    (tmp_path / "_ctx" / "prime_test.md").write_text("---\nsegment: test\n---\n# Prime\n")
    (tmp_path / "_ctx" / "session_test.md").write_text("# Session\n")
    (tmp_path / "_ctx" / "trifecta_config.json").write_text(
        '{\n  "segment": "test",\n  "scope": "test",\n  "repo_root": "' + str(tmp_path) + '"\n}\n'
    )

    yield tmp_path


def test_indexes_skills_directory(temp_segment):
    """Verify that skills/**/*.md files are indexed."""
    use_case = BuildContextPackUseCase(FileSystemAdapter())
    result = use_case.execute(temp_segment)

    assert result.is_ok(), f"Build failed: {result.unwrap_error()}"

    pack = result.unwrap()
    skill_chunks = [c for c in pack.chunks if "skills/" in c.source_path]

    assert len(skill_chunks) > 0, "No skills/ files indexed"
    assert any("test-skill" in c.source_path for c in skill_chunks)


def test_indexes_apps_directory(temp_segment):
    """Verify that apps/**/*.py files are indexed."""
    use_case = BuildContextPackUseCase(FileSystemAdapter())
    result = use_case.execute(temp_segment)

    assert result.is_ok(), f"Build failed: {result.unwrap_error()}"

    pack = result.unwrap()
    app_chunks = [c for c in pack.chunks if "apps/" in c.source_path]

    assert len(app_chunks) > 0, "No apps/ files indexed"
    assert any("main.py" in c.source_path for c in app_chunks)


def test_indexes_config_directory(temp_segment):
    """Verify that config/**/*.yaml files are indexed."""
    use_case = BuildContextPackUseCase(FileSystemAdapter())
    result = use_case.execute(temp_segment)

    assert result.is_ok(), f"Build failed: {result.unwrap_error()}"

    pack = result.unwrap()
    config_chunks = [c for c in pack.chunks if "config/" in c.source_path]

    assert len(config_chunks) > 0, "No config/ files indexed"
    assert any("settings.yaml" in c.source_path for c in config_chunks)


def test_indexes_tests_directory(temp_segment):
    """Verify that tests/**/*.py files are indexed."""
    use_case = BuildContextPackUseCase(FileSystemAdapter())
    result = use_case.execute(temp_segment)

    assert result.is_ok(), f"Build failed: {result.unwrap_error()}"

    pack = result.unwrap()
    test_chunks = [c for c in pack.chunks if "tests/" in c.source_path]

    assert len(test_chunks) > 0, "No tests/ files indexed"
    assert any("test_main.py" in c.source_path for c in test_chunks)


def test_indexes_entry_points(temp_segment):
    """Verify that entry point files (main.py, app.py) are indexed."""
    use_case = BuildContextPackUseCase(FileSystemAdapter())
    result = use_case.execute(temp_segment)

    assert result.is_ok(), f"Build failed: {result.unwrap_error()}"

    pack = result.unwrap()

    # Check that main.py in apps/ is indexed
    assert any("main.py" in c.source_path for c in pack.chunks)


def test_chunk_count_increased(temp_segment):
    """Verify that adding custom directories increases chunk count significantly."""
    use_case = BuildContextPackUseCase(FileSystemAdapter())
    result = use_case.execute(temp_segment)

    assert result.is_ok(), f"Build failed: {result.unwrap_error()}"

    pack = result.unwrap()

    # Should have at least:
    # - 1 skill.md
    # - 3 ctx files
    # - 1 docs file
    # - 1 skills file
    # - 1 apps file
    # - 1 config file
    # - 1 tests file
    assert len(pack.chunks) >= 8, f"Expected >= 8 chunks, got {len(pack.chunks)}"
