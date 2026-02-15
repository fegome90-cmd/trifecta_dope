# TestSprite CLI Workaround

> Converting TestSprite test plans to pytest for CLI tools

---

## Problem

TestSprite requires a running HTTP server on port 8000. CLI tools like `trifecta` cannot use TestSprite's execution engine.

## Solution

Use TestSprite for **planning**, then convert the test plan to pytest manually.

---

## Conversion Template

### TestSprite Test Plan

```json
{
  "id": "TC001",
  "title": "test_context_pack_build_success",
  "description": "Verify that running 'trifecta ctx build' on a valid segment creates the context_pack.json file successfully."
}
```

### Converted pytest Test

```python
# tests/testsprite/test_context_pack.py
"""Tests generated from TestSprite test plan."""

import subprocess
import tempfile
import shutil
from pathlib import Path

import pytest


class TestContextPackBuild:
    """TC001-TC002: Context Pack Build Tests"""

    @pytest.fixture
    def temp_segment(self, tmp_path: Path) -> Path:
        """Create a minimal valid segment structure."""
        segment = tmp_path / "test_segment"
        segment.mkdir()

        # Create _ctx directory with required files
        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()

        # Minimal config
        config = {
            "segment": "test_segment",
            "scope": "Test segment",
            "repo_root": str(segment),
            "last_verified": "2026-02-15"
        }
        import json
        (ctx_dir / "trifecta_config.json").write_text(json.dumps(config, indent=2))

        # Create required context files
        (ctx_dir / "agent_test_segment.md").write_text("# Agent\n")
        (ctx_dir / "prime_test_segment.md").write_text("# Prime\n")
        (ctx_dir / "session_test_segment.md").write_text("# Session\n")

        # AGENTS.md
        (segment / "AGENTS.md").write_text("# AGENTS\n\nRead skill.md.\n")

        return segment

    def test_TC001_context_pack_build_success(self, temp_segment: Path):
        """TC001: Verify ctx build creates context_pack.json."""
        result = subprocess.run(
            ["uv", "run", "trifecta", "ctx", "build", "-s", str(temp_segment)],
            capture_output=True,
            text=True,
            cwd=temp_segment
        )

        # Check exit code
        assert result.returncode == 0, f"Build failed: {result.stderr}"

        # Verify context_pack.json created
        pack_path = temp_segment / "_ctx" / "context_pack.json"
        assert pack_path.exists(), "context_pack.json not created"

    def test_TC002_context_pack_build_failure_missing_ctx(self, tmp_path: Path):
        """TC002: Verify ctx build errors on missing _ctx/."""
        segment = tmp_path / "empty_segment"
        segment.mkdir()
        # No _ctx directory

        result = subprocess.run(
            ["uv", "run", "trifecta", "ctx", "build", "-s", str(segment)],
            capture_output=True,
            text=True,
            cwd=segment
        )

        # Should fail
        assert result.returncode != 0, "Build should fail without _ctx"
        assert "error" in result.stderr.lower() or "failed" in result.stderr.lower()


class TestContextPackValidate:
    """TC003-TC004: Context Pack Validation Tests"""

    def test_TC003_validate_success(self, temp_segment: Path):
        """TC003: Validate passes on valid context pack."""
        # First build
        subprocess.run(
            ["uv", "run", "trifecta", "ctx", "build", "-s", str(temp_segment)],
            capture_output=True
        )

        # Then validate
        result = subprocess.run(
            ["uv", "run", "trifecta", "ctx", "validate", "-s", str(temp_segment)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "passed" in result.stdout.lower() or "✅" in result.stdout

    def test_TC004_validate_failure(self, temp_segment: Path):
        """TC004: Validate fails on corrupted pack."""
        # Create corrupted pack
        pack_path = temp_segment / "_ctx" / "context_pack.json"
        pack_path.write_text("{ invalid json }")

        result = subprocess.run(
            ["uv", "run", "trifecta", "ctx", "validate", "-s", str(temp_segment)],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0


class TestContextSearch:
    """TC007-TC008: Context Search Tests"""

    @pytest.fixture
    def segment_with_pack(self, temp_segment: Path) -> Path:
        """Create segment with built context pack."""
        subprocess.run(
            ["uv", "run", "trifecta", "ctx", "build", "-s", str(temp_segment)],
            capture_output=True
        )
        return temp_segment

    def test_TC007_search_with_results(self, segment_with_pack: Path):
        """TC007: Search returns chunk IDs."""
        result = subprocess.run(
            ["uv", "run", "trifecta", "ctx", "search",
             "-s", str(segment_with_pack),
             "-q", "context"],
            capture_output=True,
            text=True
        )

        # Check for chunk IDs in output (format: prime:xxx or similar)
        assert "prime:" in result.stdout or "chunk" in result.stdout.lower()

    def test_TC008_search_no_results(self, segment_with_pack: Path):
        """TC008: Search handles zero results gracefully."""
        result = subprocess.run(
            ["uv", "run", "trifecta", "ctx", "search",
             "-s", str(segment_with_pack),
             "-q", "zzzznonexistentterm12345"],
            capture_output=True,
            text=True
        )

        # Should not crash, may return empty or message
        assert result.returncode == 0 or "no" in result.stdout.lower() or "0" in result.stdout
```

---

## Complete Test Plan Conversion

| TestSprite ID | pytest Method | Status |
|---------------|---------------|--------|
| TC001 | `test_TC001_context_pack_build_success` | ✅ Converted |
| TC002 | `test_TC002_context_pack_build_failure_missing_ctx` | ✅ Converted |
| TC003 | `test_TC003_validate_success` | ✅ Converted |
| TC004 | `test_TC004_validate_failure` | ✅ Converted |
| TC005 | (similar pattern) | 📝 Template ready |
| TC006 | (similar pattern) | 📝 Template ready |
| TC007 | `test_TC007_search_with_results` | ✅ Converted |
| TC008 | `test_TC008_search_no_results` | ✅ Converted |
| TC009 | (get chunk test) | 📝 Template ready |
| TC010 | (get chunk not found) | 📝 Template ready |

---

## Running the Converted Tests

```bash
# Run all TestSprite-converted tests
uv run pytest tests/testsprite/ -v

# Run specific test class
uv run pytest tests/testsprite/test_context_pack.py::TestContextPackBuild -v

# Run with coverage
uv run pytest tests/testsprite/ --cov=src --cov-report=term-missing
```

---

## Workflow Summary

```
1. TestSprite Planning
   ├── testsprite_bootstrap (if needed)
   ├── testsprite_generate_code_summary (AI generates YAML)
   └── testsprite_generate_backend_test_plan

2. Manual Conversion
   ├── Read test plan JSON
   ├── Create pytest file per feature
   ├── Use subprocess for CLI calls
   └── Add fixtures for setup/teardown

3. Execution
   └── uv run pytest tests/testsprite/ -v
```

---

## Key Differences from TestSprite Execution

| Aspect | TestSprite | pytest Conversion |
|--------|------------|-------------------|
| Test runner | Cloud via tunnel | Local subprocess |
| Server required | Yes (port 8000) | No |
| CLI support | ❌ Limited | ✅ Full |
| Browser testing | ✅ Built-in | ❌ Requires Playwright |
| Test isolation | TestSprite-managed | pytest fixtures |
| Reporting | Dashboard | pytest output + coverage |
