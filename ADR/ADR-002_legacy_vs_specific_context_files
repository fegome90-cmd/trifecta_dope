ADR-002: Legacy vs Specific Context Files Naming Convention

Status: Proposed (ready to adopt)

Date: 2026-01-05

Context: Trifecta CLI (create, reset, ctx build) uses inconsistent naming for context files (agent.md, prime.md, session.md)

Decision

We will enforce the **specific naming convention** (agent_{segment_id}.md) across all CLI commands and deprecate the **legacy naming convention** (agent.md, prime.md, session.md).

The `reset` command will be updated to use specific filenames, and existing legacy files will be treated as errors during validation.

Why

We discovered an inconsistency where two `agent.md` files coexist in `_ctx/`:

1. `_ctx/agent.md` - Legacy format (generic, no suffix)
2. `_ctx/agent_trifecta_dope.md` - Specific format (with segment_id suffix)

This inconsistency causes:

**Confusion**: Developers don't know which file is the source of truth

**Validation ambiguity**: The system allows legacy files to coexist with specific files, violating the "3+1 contract"

**Command inconsistency**: 
- `create` command writes: `agent_{segment_id}.md` (specific)
- `reset` command writes: `agent.md` (legacy)
- `file_system.py` reads: `agent.md` (legacy)

**Fail-closed violation**: Legacy files are detected as errors in `ctx build` but are still created by `reset`

Evidence

**File System State** (2026-01-05):
```
_ctx/
├── agent.md                    # Legacy (2362 bytes)
└── agent_trifecta_dope.md     # Specific (4296 bytes)
```

**Code Evidence**:

1. [`cli.py:1142`](../src/infrastructure/cli.py:1142) - `create` command uses specific format:
   ```python
   f"_ctx/agent_{segment_id}.md": template_renderer.render_agent(config),
   ```

2. [`cli.py:1061`](../src/infrastructure/cli.py:1061) - `reset` command uses legacy format:
   ```python
   (Path(segment) / "_ctx" / "agent.md").write_text(template_renderer.render_agent(config))
   ```

3. [`validators.py:127`](../src/infrastructure/validators.py:127) - Legacy files defined as errors:
   ```python
   legacy_names = ["agent.md", "prime.md", "session.md"]
   ```

4. [`cli.py:222`](../src/infrastructure/cli.py:222) - `ctx build` fails on legacy files:
   ```python
   if legacy:
       typer.echo("❌ Legacy context files detected (Fail-Closed):")
   ```

5. [`file_system.py:24`](../src/infrastructure/file_system.py:24) - Reads legacy format:
   ```python
   agent_path = ctx_dir / "agent.md"
   ```

Naming Convention

**Legacy Format (DEPRECATED)**:
- `_ctx/agent.md`
- `_ctx/prime.md`
- `_ctx/session.md`

**Specific Format (REQUIRED)**:
- `_ctx/agent_{segment_id}.md`
- `_ctx/prime_{segment_id}.md`
- `_ctx/session_{segment_id}.md`

Where `segment_id = normalize_segment_id(path.name)`

Examples:
- Segment `trifecta_dope` → `agent_trifecta_dope.md`
- Segment `debug_terminal` → `agent_debug_terminal.md`
- Segment `eval-harness` → `agent_eval_harness.md`

Implementation Plan

**Phase 1: Fix `reset` Command (Immediate)**
- Update [`cli.py:1061`](../src/infrastructure/cli.py:1061) to write specific filenames
- Update [`cli.py:1062-1065`](../src/infrastructure/cli.py:1062) for prime and session files
- Add unit test for `reset` command output filenames

**Phase 2: Fix `file_system.py` (Immediate)**
- Update [`file_system.py:24`](../src/infrastructure/file_system.py:24) to read specific filenames
- Update [`file_system.py:23`](../src/infrastructure/file_system.py:23) for prime file
- Update [`file_system.py:25`](../src/infrastructure/file_system.py:25) for session file
- Add unit tests for file path resolution

**Phase 3: Cleanup Existing Legacy Files (Manual)**
- Delete `_ctx/agent.md` from trifecta_dope segment
- Run `ctx validate` to confirm no legacy files remain
- Update documentation to reflect specific format only

**Phase 4: Update Documentation (Immediate)**
- Update [`README.md`](../README.md) to show specific format examples
- Update [`templates.py`](../src/infrastructure/templates.py:66) comments to reference specific format
- Update [`validators.py`](../src/infrastructure/validators.py:54) docstring for clarity

Consequences

Positive

- **Single source of truth**: Only one agent.md file per segment
- **Consistent naming**: All commands use the same format
- **Fail-closed compliance**: Legacy files are properly rejected
- **Clear validation**: Ambiguity detection works correctly

Costs / Tradeoffs

- **Breaking change**: Existing segments with legacy files need manual cleanup
- **Migration effort**: Developers must rename files in existing segments
- **Documentation updates**: All examples must use specific format

Migration Guide

For existing segments with legacy files:

```bash
# 1. Identify legacy files
cd /path/to/segment
ls _ctx/agent.md _ctx/prime.md _ctx/session.md

# 2. Rename to specific format
SEGMENT_ID=$(basename $(pwd) | sed 's/-/_/g')
mv _ctx/agent.md _ctx/agent_${SEGMENT_ID}.md
mv _ctx/prime.md _ctx/prime_${SEGMENT_ID}.md
mv _ctx/session.md _ctx/session_${SEGMENT_ID}.md

# 3. Validate
trifecta ctx validate --segment .
```

Alternatives Considered

**Alternative 1: Support Both Formats**
- Allow both legacy and specific formats to coexist
- **Rejected**: Violates fail-closed principle, causes ambiguity

**Alternative 2: Deprecate Gradually**
- Issue warnings for legacy files but allow them
- **Rejected**: Inconsistent with fail-closed validation, delays cleanup

**Alternative 3: Auto-Migrate**
- Automatically rename legacy files on `ctx build`
- **Rejected**: Silent file renaming is dangerous, breaks reproducibility

References

- [`validators.py`](../src/infrastructure/validators.py:48) - `validate_segment_structure()` function
- [`cli.py`](../src/infrastructure/cli.py:1101) - `create` and `reset` commands
- [`file_system.py`](../src/infrastructure/file_system.py:1) - File system adapter
- [`docs/bugs/create_cwd_bug.md`](../docs/bugs/create_cwd_bug.md) - Related bug report
- ADR-001: Micro-Audit Patterns Scan Before Feature Work
