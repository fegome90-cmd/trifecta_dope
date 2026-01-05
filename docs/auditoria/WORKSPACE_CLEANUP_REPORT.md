# Workspace Cleanup Report

**Date**: 2026-01-05
**Scope**: Analysis of demo_workspace, scoop, and tools directories
**Status**: ✅ MIGRATION COMPLETED

## Executive Summary

After analyzing three directories, **all three violate Clean Architecture** defined in [`README.md`](../README.md:64). While directories contain legitimate content, they are **misplaced** and do not follow the project's established structure.

### Architecture Violations

| Directory | Current Location | Should Be | Violation Type |
|-----------|-----------------|-------------|----------------|
| `demo_workspace/` | Root | `tests/fixtures/` or `tests/demo/` | Test structure |
| `scoop/` | Root | `packaging/` or `distribution/` | Distribution structure |
| `tools/` | Root | `scripts/debug/` | Scripts structure |

### Reference Architecture

From [`README.md`](../README.md:64):
```
trifecta_dope/
├── src/
│   ├── domain/           # Entidades de negocio (Pydantic models)
│   ├── application/      # Use cases (lógica de negocio)
│   └── infrastructure/   # Implementaciones concretas
├── tests/                # Unit tests (pytest)
├── braindope.md          # Especificación completa
└── README.md             # Este archivo
```

**Expected structure for auxiliary directories**:
- `tests/` - All test fixtures and demo code
- `scripts/` - All utility and debugging scripts
- `packaging/` or `distribution/` - Installation manifests and packaging

---

## Directory Analysis

### 1. `demo_workspace/` ⚠️ ARCHITECTURE VIOLATION

**Current Location**: Root  
**Should Be**: `tests/fixtures/demo_workspace/` or `tests/demo/`

**Purpose**: Testing/Demonstration workspace

**Contents**:
```
demo_workspace/
├── demo.py                    # Simple test class
├── demo_pr2_sample.py         # Another test class
└── .trifecta/
    ├── _ctx/
    │   └── telemetry/
    │       ├── events.jsonl     # Generated telemetry data
    │       ├── last_run.json    # Generated telemetry data
    │       └── metrics.json    # Generated telemetry data
```

**Issues**:
1. **Architecture violation**: Test fixtures should be in `tests/fixtures/`
2. **Not in .gitignore**: This directory is tracked by git but contains generated artifacts
3. **Generated telemetry**: `.trifecta/_ctx/telemetry/` contains runtime-generated files

**Evidence**:
- [`demo.py`](../demo_workspace/demo.py:1): Simple class `A` with method `foo()`
- [`demo_pr2_sample.py`](../demo_workspace/demo_pr2_sample.py:1): Simple class `Demo` with method `hi()`
- Telemetry files: `events.jsonl`, `last_run.json`, `metrics.json`

**Recommendation**: Move to `tests/fixtures/demo_workspace/` and add to `.gitignore`

---

### 2. `scoop/` ⚠️ ARCHITECTURE VIOLATION

**Current Location**: Root  
**Should Be**: `packaging/scoop/` or `distribution/scoop/`

**Purpose**: Scoop package manager manifest for Windows installation

**Contents**:
```
scoop/
├── README.md                  # Installation documentation
└── trifecta.json             # Scoop manifest file
```

**Issues**:
1. **Architecture violation**: Packaging/distribution files should be in dedicated directory
2. **Inconsistent**: Other packaging tools may be added, creating root-level clutter

**Analysis**:
- **Legitimate content**: Contains official installation manifest for Windows users
- **Well-documented**: README.md provides complete installation instructions
- **Versioned**: Manifest includes version 0.1.0, dependencies, and auto-update config

**Evidence**:
- [`scoop/README.md`](../scoop/README.md:1): Complete installation guide for Scoop
- [`scoop/trifecta.json`](../scoop/trifecta.json:1): Proper Scoop manifest with:
  - Version: 0.1.0
  - Dependencies: python, uv
  - Installation scripts
  - Auto-update configuration

**Recommendation**: Move to `packaging/scoop/` to align with Clean Architecture

---

### 3. `tools/` ⚠️ ARCHITECTURE VIOLATION

**Current Location**: Root  
**Should Be**: `scripts/debug/` or `scripts/utils/`

**Purpose**: Development and debugging utilities

**Contents**:
```
tools/
└── probe_lsp_ready.py        # LSP readiness probe script
```

**Issues**:
1. **Architecture violation**: Utility scripts should be in `scripts/` directory
2. **Inconsistent**: Other scripts are in `scripts/` (e.g., `debug/debug_*.py`)

**Analysis**:
- **Legitimate development tool**: Script to probe LSP daemon readiness
- **Well-structured**: Uses proper imports and mock telemetry
- **Useful for debugging**: Helps verify LSP daemon state during development

**Evidence**:
- [`tools/probe_lsp_ready.py`](../tools/probe_lsp_ready.py:1): Script that:
  - Probes LSP client readiness
  - Waits up to 5 seconds for READY state
  - Reports success/failure with detailed state
  - Uses mock telemetry for testing

**Recommendation**: Move to `scripts/debug/probe_lsp_ready.py` to align with existing script structure

---

## Recommendations

### Immediate Actions

1. **Create proper directory structure**:
   ```bash
   mkdir -p tests/fixtures
   mkdir -p packaging
   mkdir -p scripts/debug
   ```

2. **Move directories to correct locations**:
   ```bash
   # Move demo workspace
   mv demo_workspace tests/fixtures/demo_workspace
   
   # Move scoop manifest
   mv scoop packaging/scoop
   
   # Move debugging tools
   mv tools scripts/debug
   ```

3. **Update `.gitignore`**:
   ```gitignore
   # Demo/testing workspaces
   tests/fixtures/demo_workspace/.trifecta/_ctx/telemetry/
   ```

4. **Update references**:
   - Update [`README.md`](../README.md:1) to reference new locations
   - Update documentation that references `scoop/` or `tools/`
   - Update CI/CD pipelines if they reference these directories

### No Action Required

- **Content is legitimate**: All three directories contain useful project assets
- **Only location is wrong**: Content should be preserved, just moved

---

## Related Issues

This analysis is related to:
- **ADR-002**: Legacy vs Specific Context Files Naming Convention
- **ADR-001**: Micro-Audit Patterns Scan Before Feature Work
- [`docs/bugs/create_cwd_bug.md`](../docs/bugs/create_cwd_bug.md:1): Related to `create` command behavior

The `demo_workspace` directory may have been created during testing of `create` command, demonstrating the need for proper test fixture organization.

---

## Appendix: Existing Script Structure

Current [`scripts/`](../scripts/) directory:
```
scripts/
├── debug/                    # Debugging utilities
│   ├── debug_client.py
│   ├── debug_status.py
│   └── debug_ts.py
├── install_FP.py              # Installation script
├── ingest_trifecta.py        # Legacy ingestion script
└── DEPRECATED_ingest_trifecta.py.md
```

**Pattern**: Debugging scripts are in `scripts/debug/`, so `tools/probe_lsp_ready.py` should follow this pattern.

---

## Appendix: .gitignore Status

Current [`.gitignore`](../.gitignore:1) entries:
- ✅ `_ctx/telemetry/` (line 42) - Covers telemetry in main segment
- ❌ `demo_workspace/` - **MISSING** - Should be added or moved
- ✅ `tmp_*` (line 43) - Covers temporary directories
- ✅ `example-segment/` (line 25) - Covers generated segments

**Recommendation**: After moving directories, update `.gitignore` to cover generated artifacts in new locations.
