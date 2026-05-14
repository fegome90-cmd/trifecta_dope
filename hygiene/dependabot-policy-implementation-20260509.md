# Dependabot Policy Implementation Report — 2026-05-09

> **Status**: APPLIED
> **Change**: `git-hygiene-dependabot-policy` (follow-up #3 apply)
> **Authority scope**: Replaces previous `.github/dependabot.yml` with approved conservative config.
> **Policy authority**: `hygiene/dependabot-policy-20260509.md`

---

## 1. Config Anterior (Resumen)

| Setting | Valor Anterior |
|---------|---------------|
| `open-pull-requests-limit` (pip) | **10** |
| `open-pull-requests-limit` (actions) | **5** |
| Groups (pip) | `dev-dependencies` (pytest*/ruff/mypy/pyright), `production-dependencies` (typer*/pydantic/pyyaml/tree-sitter*) |
| Ignore rules | **Ninguno** |
| Timezone | No set |
| Labels (pip) | `dependencies`, `python` |
| Labels (actions) | `dependencies`, `github-actions` |

**Problemas**: Límites demasiado altos generaban colas ruidosas. Sin ignores = Dependabot propondría majors de HIGH packages. Grupos demasiado amplios sin separación de riesgo.

## 2. Config Nueva (Resumen)

| Setting | Valor Nuevo |
|---------|------------|
| `open-pull-requests-limit` (pip) | **3** |
| `open-pull-requests-limit` (actions) | **2** |
| Timezone | **UTC** (explícito) |
| Labels (pip) | `dependencies`, `python` (sin cambios) |
| Labels (actions) | `dependencies`, `github-actions` (sin cambios) |
| No auto-merge | Confirmado |

### 2.1 Groups Nuevos (5)

| Group | Patterns | Update Types |
|-------|----------|-------------|
| `dev-test-deps` | pytest*, pytest-env, pytest-cov | minor, patch |
| `dev-lint-type` | ruff, mypy, pyrefly, types-* | minor, patch |
| `prod-core` | pydantic, pyyaml, ruamel.yaml, jsonschema | patch only |
| `prod-parser` | tree-sitter* | patch only |
| `prod-cli` | typer* | patch only |

### 2.2 Ignore Rules (10 HIGH packages)

Todos los HIGH packages ignoran **semver-major + semver-minor** (patch-only por Dependabot):

| # | Package | Categoría | Update-types ignorados |
|---|---------|-----------|----------------------|
| 1 | `typer*` | HIGH — CLI framework (0.x) | semver-major, semver-minor |
| 2 | `tree-sitter*` | HIGH — AST parser (0.x) | semver-major, semver-minor |
| 3 | `ruamel.yaml` | HIGH — YAML round-trip (0.x) | semver-major, semver-minor |
| 4 | `tiktoken` | HIGH — Tokenization (0.x) | semver-major, semver-minor |
| 5 | `pandas` | HIGH — Data stack | semver-major, semver-minor |
| 6 | `pydantic` | HIGH — Data validation | semver-major, semver-minor |
| 7 | `filelock` | HIGH — File locking | semver-major, semver-minor |
| 8 | `jsonschema` | HIGH — Schema validation | semver-major, semver-minor |
| 9 | `pyyaml` | HIGH — YAML parsing | semver-major, semver-minor |
| 10 | `PyYAML` | HIGH — YAML parsing (alt name) | semver-major, semver-minor |

## 3. Límites Nuevos

- **pip**: 3 PRs abiertos máximo (reducido de 10)
- **github-actions**: 2 PRs abiertos máximo (reducido de 5)

## 4. Validaciones Realizadas

| Validación | Resultado |
|-----------|-----------|
| No tabs (YAML requiere spaces) | PASS |
| YAML parse (PyYAML) | Manual schema validation only (PyYAML no instalado) |
| Schema: group update-types valores aceptados (minor/patch) | PASS — 5 groups con valores correctos |
| Schema: ignore update-types valores aceptados (semver-major/semver-minor) | PASS — 10 deps × 2 types = 20 entries |
| Pip limit = 3 | PASS |
| Actions limit = 2 | PASS |
| No auto-merge | PASS |
| Timezone UTC explícito | PASS |
| 10 HIGH packages con semver-minor + semver-major ignores | PASS |
| 5 groups (dev-test-deps, dev-lint-type, prod-core, prod-parser, prod-cli) | PASS |

## 5. Acciones NO Tomadas

1. ❌ `pyproject.toml` NO modificado
2. ❌ `uv.lock` NO modificado
3. ❌ Dependencias NO actualizadas
4. ❌ Código funcional NO tocado
5. ❌ Ramas/tags NO creados/modificados
6. ❌ `--no-verify` NO utilizado
7. ❌ Auto-merge NO habilitado
8. ❌ mypy floor update NO ejecutado
9. ❌ typer version gap NO resuelto
10. ❌ PRs manuales NO abiertos

## 6. Riesgos Residuales

| Risk | Severity | Mitigación |
|------|----------|-----------|
| **mypy floor no actualizado** | MEDIUM | PR #96 cerrado; mypy >=1.20.1 update requiere SDD cycle separado |
| **typer major version gap** | HIGH | Floor >=0.9.0 pero latest es 0.24.x; jump diferido pero crecerá. Requires SDD/manual review |
| **Security updates necesitan CI** | MEDIUM | Security updates bypass `open-pull-requests-limit` pero aún requieren CI pasando antes de merge |
| **PyYAML duplicate ignore** | LOW | Both `pyyaml` and `PyYAML` are ignored — Dependabot may match one or both depending on registry name. No harm in covering both |
| **YAML no parseado con PyYAML** | LOW | Schema validated manually. CI will validate on push if Dependabot reads it |

---

*Generated: 2026-05-09 | Status: APPLIED | Change: git-hygiene-dependabot-policy | Implementation of approved dependabot config.*
