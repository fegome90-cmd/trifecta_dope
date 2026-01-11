"""Stub Regeneration Use Case - Regenerates _ctx/generated/ files."""

import hashlib
from pathlib import Path
from typing import Any


class StubRegenUseCase:
    """Regenerate deterministic stub files in _ctx/generated/."""

    REPO_MAP_TEMPLATE = """# {repo_name} - Repository Map

> **Generated**: {date}
> **Purpose**: High-level module navigation for ctx.plan code_navigation feature
> **Hash**: {hash}

---

## Module Overview

| Module | Path | Purpose | Entrypoints |
|--------|------|---------|-------------|
{module_rows}

---

## Clean Architecture Layers

```
[Infrastructure Layer] - CLI, File System, Telemetry
        ↓
[Application Layer] - Use Cases, Business Logic
        ↓
[Domain Layer] - Core Entities, Business Rules
```

---

## CLI Commands Reference

### `ctx` App
```bash
trifecta ctx build     # Build context pack
trifecta ctx search    # Search chunks by query
trifecta ctx get       # Get chunks by ID
trifecta ctx sync      # Build + Validate
trifecta ctx stats     # Show telemetry statistics
trifecta ctx plan      # Generate execution plan
trifecta ctx eval-plan # Evaluate plan against dataset
```

---

## Key Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `skill.md` | Development rules and protocols |
| `_ctx/prime_*.md` | Progressive Context Compression index |
| `_ctx/session_*.md` | Session history |
| `_ctx/aliases.yaml` | Feature mapping for ctx.plan |
| `_ctx/telemetry/events.jsonl` | Telemetry event log |

---

**Limitations**: This is a curated map, not exhaustive indexing. For detailed symbol navigation, use ctx.plan with symbol_surface feature.

---

**PROMPT_FIX_HINT**: If you are an agent, copy NEXT_STEPS and rerun the original command. If still failing, paste stderr + command + exit code.
"""

    SYMBOLS_STUB_TEMPLATE = """# Symbol Navigation - Stub (v1)

> **Status**: Placeholder for symbol-level navigation
> **Version**: v1 (Prime-based) → v2 (AST/LSP-based, planned)
> **Hash**: {hash}

---

## Current Approach (v1)

Symbol navigation uses PRIME index routing via ctx.plan:

- Use `ctx.plan --task "class ClassName"` for class lookup
- Use `ctx.plan --task "function function_name"` for function lookup
- Use `ctx.plan --task "method method_name()"` for method lookup

---

## v2 Roadmap

Planned features for v2 symbol navigation:

1. **AST-based indexing** - Extract all symbols from source
2. **LSP-style features** - Go-to-definition, find references
3. **Cross-references** - Call graphs, dependency analysis

---

**Note**: This stub provides policy guidance. Full symbol indexing requires AST/LSP infrastructure planned for v2.

---

**PROMPT_FIX_HINT**: If you are an agent, copy NEXT_STEPS and rerun the original command. If still failing, paste stderr + command + exit code.
"""

    MAX_REPO_MAP_LINES = 300
    MAX_SYMBOLS_STUB_LINES = 200

    def __init__(self, telemetry=None) -> None:
        self.telemetry = telemetry

    def _detect_modules(self, segment_path: Path) -> list[dict]:
        """Detect module structure from src/ directory."""
        modules: list[dict] = []
        src_dir = segment_path / "src"

        if not src_dir.exists():
            return modules

        # Detect main modules
        for layer in ["application", "domain", "infrastructure", "interfaces"]:
            layer_dir = src_dir / layer
            if layer_dir.exists():
                modules.append(
                    {
                        "name": layer.capitalize(),
                        "path": f"src/{layer}/",
                        "purpose": f"{layer.capitalize()} layer",
                        "entrypoints": "various",
                    }
                )

        return modules

    def _compute_hash(self, segment_path: Path) -> str:
        """Compute hash of segment for determinism."""
        # Hash based on directory structure and key files
        hasher = hashlib.md5(usedforsecurity=False)

        # Hash directory listing
        try:
            for p in sorted(segment_path.rglob("*")):
                if p.is_file():
                    hasher.update(str(p.relative_to(segment_path)).encode())
        except Exception:
            pass

        return hasher.hexdigest()[:12]

    def execute(self, target_path: Path) -> dict:
        """Regenerate stub files.

        Returns:
            Dict with regen_ok, stubs, and any errors/warnings
        """
        ctx_dir = target_path / "_ctx"
        generated_dir = ctx_dir / "generated"

        result: dict[str, Any] = {
            "regen_ok": True,
            "stubs": [],
            "warnings": [],
            "errors": [],
        }

        # Create generated dir if it doesn't exist
        try:
            generated_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            result["regen_ok"] = False
            result["errors"].append(f"Failed to create generated dir: {e}")
            self._log_telemetry("repo_map", False, str(e))
            return result

        segment_hash = self._compute_hash(target_path)
        repo_name_raw = target_path.name
        repo_name = (
            " ".join(
                word.capitalize()
                for word in repo_name_raw.replace("-", " ").replace("_", " ").split()
            )
            or repo_name_raw
        )

        # Generate repo_map.md
        try:
            modules = self._detect_modules(target_path)
            module_rows = ""
            for m in modules:
                module_rows += (
                    f"| {m['name']} | `{m['path']}` | {m['purpose']} | {m['entrypoints']} |\n"
                )

            repo_map_content = self.REPO_MAP_TEMPLATE.format(
                repo_name=repo_name,
                hash=segment_hash,
                module_rows=module_rows
                if module_rows
                else "| (No modules detected) | - | - | - |\n",
                date="__DATE__",  # Placeholder for reproducibility
            )

            repo_map_path = generated_dir / "repo_map.md"

            # Check cap
            line_count = len(repo_map_content.splitlines())
            if line_count > self.MAX_REPO_MAP_LINES:
                result["warnings"].append(f"repo_map.md exceeds cap: {line_count} lines")

            repo_map_path.write_text(repo_map_content)
            result["stubs"].append("repo_map.md")

        except Exception as e:
            result["regen_ok"] = False
            result["errors"].append(f"repo_map.md: {e}")
            self._log_telemetry("repo_map", False, str(e))

        # Generate symbols_stub.md
        try:
            symbols_stub_content = self.SYMBOLS_STUB_TEMPLATE.format(hash=segment_hash)

            symbols_stub_path = generated_dir / "symbols_stub.md"

            # Check cap
            line_count = len(symbols_stub_content.splitlines())
            if line_count > self.MAX_SYMBOLS_STUB_LINES:
                result["warnings"].append(f"symbols_stub.md exceeds cap: {line_count} lines")

            symbols_stub_path.write_text(symbols_stub_content)
            result["stubs"].append("symbols_stub.md")

        except Exception as e:
            result["regen_ok"] = False
            result["errors"].append(f"symbols_stub.md: {e}")
            self._log_telemetry("symbols_stub", False, str(e))

        # Log success
        if result["regen_ok"] and result["stubs"]:
            for stub in result["stubs"]:
                self._log_telemetry(stub, True, None)

        return result

    def _log_telemetry(self, stub_name: str, regen_ok: bool, reason: str | None) -> None:
        """Log stub regeneration telemetry."""
        if self.telemetry:
            self.telemetry.event(
                "ctx.sync.stub_regen",
                {"stub_name": stub_name},
                {"regen_ok": regen_ok, "reason": reason or ""},
                0,  # latency not critical for this
            )
