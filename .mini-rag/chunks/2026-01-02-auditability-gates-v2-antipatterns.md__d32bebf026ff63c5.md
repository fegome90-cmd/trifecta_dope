depende de cwd |
| **CWD Independence** | `pytest tests/integration/test_cwd_independence.py::test_ast_symbols_from_other_dir -v` | Integration | FILE_NOT_FOUND (busca en cwd) | RC=0 (resuelve desde segment_root) | **AP3 TRIPWIRE**: ejecutar desde /tmp | AP3: Cambia cwd antes de llamar CLI |
| **Symbol Resolution** | `uv run trifecta ast symbols sym://python/mod/use_cases` | Integration | FILE_NOT_FOUND | status=ok OR code≠FILE_NOT_FOUND | Resolución desde segment_root/src/ | AP1: Parse JSON con jq (no string) |
| **Context Pack Schema** | `jq -e '.schema_version == 1 and .segment != null' _ctx/context_pack.json` | Integration | Schema puede estar corrupto | RC=0 (jq exit) | Validación schema sin pytest | AP1: jq es parser SSOT |
