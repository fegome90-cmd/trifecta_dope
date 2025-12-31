# Symbol Navigation - Stub (v1)

> **Status**: Placeholder for symbol-level navigation
> **Version**: v1 (Prime-based) → v2 (AST/LSP-based, planned)

---

## Current Approach (v1)

Symbol navigation in Trifecta v1 uses **PRIME index routing**:

1. **For classes**: Use `ctx.plan` with `symbol_surface` feature
   - Example: "class Telemetry initialization"
   - Routes to: `src/infrastructure/telemetry.py`

2. **For functions**: Use `ctx.plan` with relevant feature
   - Example: "function _estimate_tokens implementation"
   - Routes to: `src/infrastructure/telemetry.py`

3. **For methods**: Use `ctx.plan` with `symbol_surface` feature
   - Example: "method flush() implementation details"
   - Routes to: `src/infrastructure/telemetry.py`

4. **For imports**: Use `ctx.plan` with code_navigation feature
   - Example: "import statements in telemetry_reports.py"
   - Routes to: `src/infrastructure/telemetry.py` (via repo_map)

---

## Limitations (v1)

- ❌ No AST-based symbol extraction
- ❌ No LSP-style definition lookup
- ❌ No cross-reference support
- ❌ Manual symbol-to-file mapping required

---

## v2 Roadmap

Planned features for v2 symbol navigation:

1. **AST-based indexing**
   - Extract all symbols (classes, functions, methods)
   - Build symbol-to-location index
   - Support inheritance hierarchies

2. **LSP-style features**
   - Go-to-definition
   - Find references
   - Symbol search (fuzzy match)

3. **Cross-references**
   - Call graphs
   - Dependency analysis
   - Import chains

---

## Current Workarounds

| Need | Current Solution |
|------|------------------|
| Find a class | `ctx.plan --task "class ClassName initialization"` |
| Find a function | `ctx.plan --task "function function_name implementation"` |
| Find a method | `ctx.plan --task "method method_name() implementation"` |
| List symbols in file | `ctx.plan --task "symbols in filename"` → read file directly |
| Understand module | `ctx.plan --task "architecture overview module_name"` |

---

## Example Usage

```bash
# Find Telemetry class
trifecta ctx plan -s . --task "class Telemetry initialization"

# Find a specific function
trifecta ctx plan -s . --task "function _estimate_tokens implementation"

# Find a method
trifecta ctx plan -s . --task "method flush() implementation details"

# Navigate CLI symbols
trifecta ctx plan -s . --task "symbols in cli.py for ctx commands"
```

---

**Note**: This stub provides policy guidance for symbol navigation. Full symbol indexing requires AST/LSP infrastructure planned for v2.
