# WO-0010: Config Patterns per Repo - Technical Specification

**Fecha**: 2026-03-06  
**WO ID**: WO-0010  
**Epic**: E-0001 (Context Indexing)  
**Prioridad**: P1 (Recommended)  
**Status**: DRAFT  
**Owner**: TBD

---

## 1. Context

### Problem Statement
WO-0009 (P0 Fix) added 19 hardcoded patterns to index custom directories (skills/, apps/, config/, tests/). This covers ~90% of common cases but users may need to index directories not covered by the hardcoded list.

**Limitation**: New directories require code changes.

### Proposed Solution
Add optional configuration field to `_ctx/trifecta_config.json` that allows users to customize which directories are indexed.

**Benefits**:
- No code changes needed for custom patterns
- Backward compatible (default behavior unchanged)
- Simple to implement (2-3 hours)
- Easy to test (schema validation)
- Flexible (users control patterns explicitly)

---

## 2. Implementation Details

### Schema Extension (`src/domain/models.py`)

```python
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional

class IndexPatterns(BaseModel):
    """Custom index patterns configuration."""
    include: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)

class TrifectaConfig(BaseModel):
    # Existing fields
    segment: str
    scope: str
    repo_root: Path
    python_version: str = ">=3.12"
    package_manager: str = "uv"
    
    # NEW OPTIONAL field
    index_patterns: Optional[IndexPatterns] = None
```

### Use Case Changes (`src/application/use_cases.py`)

```python
# Default patterns from WO-0009 (P0 Fix)
DEFAULT_PATTERNS = [
    "docs/**/*.md",
    "src/**/*.py",
    "src/**/*.ts",
    "src/**/*.js",
    "README*.md",
    "*.md",
    "skills/**/*.md",
    "apps/**/*.py",
    "apps/**/*.ts",
    "apps/**/*.js",
    "apps/**/*.vue",
    "apps/**/*.md",
    "config/**/*.yaml",
    "config/**/*.yml",
    "config/**/*.json",
    "config/**/*.toml",
    "tests/**/*.py",
    "tests/**/*.ts",
    "tests/**/*.js",
    "main.py",
    "app.py"
]

def build_patterns_list(config: Optional[TrifectaConfig]) -> list[str]:
    """Build patterns from config or use defaults."""
    if config and config.index_patterns:
        custom_patterns = config.index_patterns.include
        if custom_patterns:
            return custom_patterns
    return DEFAULT_PATTERNS

# In BuildContextPackUseCase.execute():
patterns = build_patterns_list(config)
for pattern in patterns:
    for file_path in target_path.glob(pattern):
        # ... existing indexing logic
```

### Config File Example

```json
// _ctx/trifecta_config.json
{
  "segment": "my-project",
  "scope": "verification",
  "repo_root": "/path/to/repo",
  "python_version": ">=3.12",
  "package_manager": "uv",
  "index_patterns": {
    "include": [
      "custom/**/*.md",
      "lib/**/*.py",
      "modules/**/*.ts"
    ],
    "exclude": [
      "data/**",
      "assets/**",
      "*.generated.*"
    ]
  }
}
```

---

## 3. Tests Required

### Unit Tests (`tests/unit/test_trifecta_config_patterns.py`)

```python
def test_config_with_custom_patterns():
    """Test that custom patterns are loaded correctly."""
    config = TrifectaConfig(
        segment="test",
        scope="test",
        repo_root=Path("/tmp"),
        index_patterns=IndexPatterns(
            include=["custom/**/*.md"],
            exclude=["data/**"]
        )
    )
    patterns = build_patterns_list(config)
    assert patterns == ["custom/**/*.md"]

def test_config_without_patterns():
    """Test default behavior when no custom patterns."""
    config = TrifectaConfig(
        segment="test",
        scope="test",
        repo_root=Path("/tmp")
    )
    patterns = build_patterns_list(config)
    assert patterns == DEFAULT_PATTERNS

def test_config_none():
    """Test default behavior when config is None."""
    patterns = build_patterns_list(None)
    assert patterns == DEFAULT_PATTERNS
```

### Integration Tests (`tests/integration/test_context_pack_custom_patterns.py`)

```python
def test_custom_patterns_indexed(temp_segment_with_config):
    """Verify that custom patterns are actually used."""
    # Create custom directory with file
    (temp_segment_with_config / "custom").mkdir()
    (temp_segment_with_config / "custom" / "test.md").write_text("# Custom")
    
    # Create config with custom pattern
    config_data = {
        "segment": "test",
        "scope": "test",
        "repo_root": str(temp_segment_with_config),
        "index_patterns": {
            "include": ["custom/**/*.md"]
        }
    }
    (temp_segment_with_config / "_ctx" / "trifecta_config.json").write_text(
        json.dumps(config_data)
    )
    
    use_case = BuildContextPackUseCase(FileSystemAdapter())
    result = use_case.execute(temp_segment_with_config)
    
    assert result.is_ok()
    pack = result.unwrap()
    custom_chunks = [c for c in pack.chunks if "custom/" in c.source_path]
    assert len(custom_chunks) > 0
```

### Acceptance Tests (`tests/acceptance/test_config_patterns_e2e.py`)

```python
def test_with_custom_config():
    """E2E test with custom config file."""
    # Test full workflow with custom patterns

def test_without_config():
    """E2E test without config (default behavior)."""
    # Test that default patterns still work
```

---

## 4. Verification Commands

```bash
# Unit tests
uv run pytest tests/unit/test_trifecta_config_patterns.py -xvs

# Integration tests
uv run pytest tests/integration/test_context_pack_custom_patterns.py -xvs

# Acceptance tests (config present)
uv run pytest tests/acceptance/test_config_patterns_e2e.py::test_with_custom_config -xvs

# Acceptance tests (config absent)
uv run pytest tests/acceptance/test_config_patterns_e2e.py::test_without_config -xvs

# Verify default behavior (regression test)
uv run pytest tests/integration/test_context_pack_custom_directories.py -xvs
```

**Expected**: All tests pass.

---

## 5. Success Criteria

- ✅ Config file is optional (backward compatible)
- ✅ Default behavior unchanged (DEFAULT_PATTERNS used)
- ✅ Custom patterns are respected when configured
- ✅ Tests passing (unit + integration + acceptance)
- ✅ Documentation updated (README, skill.md)
- ✅ No regression in existing functionality
- ✅ Schema validation works correctly

---

## 6. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Schema validation errors | Strict jsonschema validation with clear error messages |
| Breaking changes | Default patterns ensure backward compatibility |
| Performance impact | Minimal (just config read, no heavy computation) |
| User confusion | Clear documentation with examples in README |

---

## 7. Estimated Effort

- **Implementation**: 2-3 hours
  - Schema extension: 30 min
  - Use case changes: 1 hour
  - Config loader: 30 min
  
- **Testing**: 2-3 hours
  - Unit tests: 1 hour
  - Integration tests: 1 hour
  - Acceptance tests: 30 min
  
- **Documentation**: 1 hour
  - README update: 30 min
  - skill.md update: 30 min

**Total**: 5-7 hours

---

## 8. Files Changed

| File | Change | Lines |
|------|--------|-------|
| `src/domain/models.py` | Add IndexPatterns schema | +15 |
| `src/application/use_cases.py` | Add build_patterns_list() | +30 |
| `tests/unit/test_trifecta_config_patterns.py` | NEW | +50 |
| `tests/integration/test_context_pack_custom_patterns.py` | NEW | +80 |
| `tests/acceptance/test_config_patterns_e2e.py` | NEW | +60 |
| `README.md` | Document custom patterns | +20 |
| `skill.md` | Add usage example | +10 |

**Total LOC**: ~265 lines

---

## 9. Dependencies

- **Blocked by**: None
- **Blocks**: P1 (Autodetection) - should be evaluated after P2 deployment
- **Related WOs**: WO-0009 (P0 Fix - completed)

---

## 10. Next Steps

1. Review and approve this specification
2. Create WO-0010 in `_ctx/jobs/pending/`
3. Implement following TDD (RED → GREEN → REFACTOR)
4. Run verification commands
5. Update documentation
6. Deploy and monitor telemetry
7. Evaluate P1 (Autodetection) after 2-4 weeks of usage data

---

**Spec Version**: 1.0  
**Created**: 2026-03-06  
**Status**: Ready for implementation
