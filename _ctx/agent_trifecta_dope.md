---
segment: trifecta_dope
scope: Trifecta Context Engine repository
repo_root: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
last_verified: 2026-03-27
default_profile: impl_patch
---

# Agent Context - Trifecta_Dope

## Source of Truth
| Sección | Fuente |
|---------|--------|
| Operational runbook | `skill.md` |
| Human onboarding | `README.md` |
| Current session evidence | `_ctx/session_trifecta_dope.md` |
| Packaging and dev dependencies | `pyproject.toml` |
| Current daemon/LSP audit evidence | `docs/reports/2026-03-26-daemon-drift-code-audit.md` |

## Tech Stack

**Lenguajes**
- Python 3.12+

**Frameworks / Libraries principales**
- Typer CLI
- Pydantic v2
- PyYAML / ruamel.yaml
- tree-sitter + tree-sitter-python
- jsonschema
- filelock
- tiktoken

**Herramientas de desarrollo**
- uv
- pytest
- ruff
- mypy
- pyright
- bandit
- safety

## Dependencies

**Runtime**
- `typer[all]`
- `pydantic`
- `pyyaml`
- `ruamel.yaml`
- `tree-sitter`
- `tree-sitter-python`
- `jsonschema`
- `filelock`
- `tiktoken`

**Development**
- `pytest`
- `pytest-cov`
- `pytest-env`
- `ruff`
- `mypy`
- `pyright`
- `bandit[toml]`
- `safety`

## Configuration

**Archivos clave**
```text
trifecta_dope/
├── pyproject.toml              # packaging + tool configuration
├── README.md                   # onboarding humano
├── skill.md                    # runbook del agente
└── _ctx/
    ├── agent_trifecta_dope.md  # estado técnico activo
    ├── prime_trifecta_dope.md  # lectura priorizada
    └── session_trifecta_dope.md # bitácora append-only
```

**Variables de entorno relevantes**
```bash
TRIFECTA_RUNTIME_DIR=           # runtime del daemon
TRIFECTA_REPO_ROOT=             # repo root usado por daemon/LSP
TRIFECTA_DAEMON_TTL=            # TTL del daemon
TRIFECTA_LSP_REQUEST_TIMEOUT=   # timeout de requests LSP
TRIFECTA_AST_PERSIST=1          # persistencia AST en tests
```

## Gates (Comandos de verificación)

**General repo gates**
```bash
uv run pytest tests/ -v
uv run ruff check src tests
uv run mypy src --no-error-summary
```

**Daemon / LSP focused gates**
```bash
uv run pytest tests/integration/test_lsp_daemon.py tests/integration/test_daemon_paths_constraints.py tests/unit/daemon/ tests/unit/test_cli_hardening.py tests/unit/test_daemon_manager.py -v
uv run ruff check src/infrastructure/daemon src/platform/daemon_manager.py tests/unit/daemon tests/unit/test_cli_hardening.py tests/unit/test_daemon_manager.py
uv run mypy src/infrastructure/daemon src/platform/daemon_manager.py --no-error-summary
```

**Context pack gates**
```bash
trifecta ctx sync --segment .
trifecta ctx validate --segment .
```

## Integration Points

**CLI / Context Engine**
- `src/infrastructure/cli.py` — main CLI entrypoint
- `src/application/search_get_usecases.py` / related use cases — context pack operations
- `src/application/status_use_case.py`, `doctor_use_case.py`, `repo_use_case.py` — repo/runtime orchestration

**Daemon / LSP**
- `src/platform/daemon_manager.py` — official lifecycle shell
- `src/application/daemon_use_case.py` — app-layer orchestration for daemon commands
- `src/infrastructure/daemon/` — extracted daemon run internals
- `src/infrastructure/lsp_client.py` — LSP client / handshake / request lifecycle
- `src/infrastructure/lsp_daemon.py` — legacy/reference daemon surface kept for compatibility/reference

**Context / Session artifacts**
- `_ctx/context_pack.json`
- `_ctx/generated/repo_map.md`
- `_ctx/generated/symbols_stub.md`
- `_ctx/session_trifecta_dope.md`

## Architecture Notes

**Design patterns in active use**
- Layered separation across `domain`, `application`, `infrastructure`, `platform`
- CLI orchestration through Typer + use cases
- Context pack workflow with search/get progressive disclosure
- Daemon shell separated from daemon runtime internals

**Key decisions**
- `uv` is the canonical runner for Python workflows
- Context operations are fail-closed on stale/invalid packs
- Review workflows (`branch-review`, `reviewctl`) should run only from a clean isolated branch/worktree
- Session evidence is append-only and should not be rewritten as mutable state

**Known limitations / active cautions**
- Context pack can become large; sync/validate may warn without failing
- README still contains historical sections and must be kept aligned conservatively
- Daemon/LSP work has recent drift reports; use session/report artifacts before assuming current batch boundaries
