---
segment: trifecta_dope
profile: load_only
---

# Prime Trifecta_Dope - Lista de Lectura

> **SEGMENT_ROOT**: `.`
> **REPO_ROOT**: `.`

Prime contiene solo paths priorizados para carga rápida.

## [HIGH] Prioridad alta - onboarding y operación actual

1. `README.md`
2. `skill.md`
3. `CLAUDE.md`
4. `_ctx/agent_trifecta_dope.md`
5. `_ctx/session_trifecta_dope.md`

## [MED] Prioridad media - daemon / LSP / contexto activo

6. `pyproject.toml`
7. `src/platform/daemon_manager.py`
8. `src/application/daemon_use_case.py`
9. `src/infrastructure/daemon/runner.py`
10. `src/infrastructure/daemon/lsp_handler.py`
11. `src/infrastructure/lsp_client.py`

## [LOW] Referencias útiles / soporte de validación

12. `tests/unit/test_daemon_manager.py`
13. `tests/unit/daemon/test_runner_repo_root.py`
14. `docs/reports/2026-03-26-daemon-drift-code-audit.md`
15. `src/infrastructure/cli.py`
16. `src/infrastructure/cli_ast.py`

## Notes

- **Última actualización**: 2026-03-27
- **Criterio**: prioriza onboarding humano, runbook operativo y superficies daemon/LSP activas antes de exploración más amplia
- **Ver también**: `skill.md` | `_ctx/agent_trifecta_dope.md` | `_ctx/session_trifecta_dope.md`
