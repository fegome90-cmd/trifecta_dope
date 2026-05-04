# Git Hygiene Roadmap v1.2 — trifecta_dope

> **Versión**: 1.2 (SSOT — locked para sprint de higiene, corregido post-veredicto)
> **Fecha**: 2026-05-04
> **Base**: SDD exploration + 3 gate iterations + Phase 1 audit ejecutada
> **Principio**: Riesgo ascendente. Cada paso es independiente, verificable y reversible.
> **Regla de oro**: Nada se borra sin SHA recording previo.
> **Audit baseline**: `origin/main` @ `86739d27f5f0f44ec4a6c63363d1894ac5439d2b`

## Reglas Obligatorias (INVARIANTES)

Estas reglas aplican a TODA ejecución del roadmap. Violación = detener inmediatamente.

1. **No borrar branches remotas** sin SHA registrado en `hygiene/sha-registry-*.md`
2. **No dropear stash** sin confirmación explícita de preservación en branch remota
3. **No hacer push destructivo** (`--force`, `--force-with-lease` solo con aprobación)
4. **No usar `--no-verify`** en ningún commit
5. **No modificar código fuente** del proyecto salvo `.mailmap` y archivos bajo `hygiene/`
6. **Baseline**: `origin/main` después de `git fetch --all --prune --tags`
7. **No guardar evidencia en `/tmp`** — TODO registro va en archivos versionables bajo `hygiene/`
8. **Si hay incertidumbre**: registrar finding y DETENER la acción destructiva

## Hallazgos del Veredicto v1.2 (Post-Audit Review)

Correcciones incorporadas tras revisión manual del output de Phase 1.

### ⚠️ TRABAJANDO EN ÁRBOL SUCIO

El working tree en `main` tiene cambios no commiteados en `.mini-rag/`, `_ctx/`, `scripts/`, `src/`, etc.
Esto **NO bloquea** borrar branches remotas fully merged, pero **SÍ bloquea** cualquier operación que implique checkout, merge, aplicar stash, pruebas o manipulación de dependabot.
**Acción**: Commitear hygiene/ en branch dedicada ANTES de cualquier otra acción.

### ⚠️ SQUASH-MERGED: EVIDENCIA INSUFICIENTE PARA DELETE DIRECTO

El reporte de Phase 1 dice que las 7 branches squash-merged tienen diffs grandes contra `origin/main` y que `git cherry` muestra todos los commits con `+`. La conclusión "contenido está en main vía squash" depende del estado del PR en GitHub, NO de equivalencia de contenido verificada localmente.
**Acción**: NO hacer `git push origin --delete` directo. Primero archivar como `archive/*` remoto, verificar que el archive existe, y recién después considerar delete del nombre original.

### ⚠️ CONTRADICCIÓN OPERACIONAL EN SUMMARY

`summary-20260504.md` propone "Archive squash-merged branches" pero los comandos hacen `git push origin --delete` directo. Eso NO archiva nada.
**Acción**: Corregido en este roadmap. El flujo correcto es: push a archive/* → verificar → delete original.

### ⚠️ INCONSISTENCIA TYPO EN DEPENDABOT

En `branch-audit` aparece `origin/dependabot/pip/pypy-gte-3.0.2` pero en `sha-registry` y `summary` aparece `pandas-gte-3.0.2`.
**Acción**: No tocar dependabot branches hasta confirmar nombre real con `git branch -r | grep dependabot`.

### ⚠️ STASH: PRESERVACIÓN MÍNIMA, NO ROBUSTA

El patch (~100MB) es preservación mínima. Para robustez real falta una branch/commit permanente.
**Acción**: Crear branch remota `hygiene/stash-preserve-codex-freeze` con el contenido del stash ANTES de cualquier otra operación.

### ✅ LO QUE ESTÁ SÓLIDO

- 4 fully merged branches: `Is-Ancestor YES` válido para safe delete remoto.
- SHA registry funciona como inventario base de rollback.
- Closed-PR branches correctamente clasificadas como `DO_NOT_DELETE`.
- Stash explícitamente marcado como no-dropeable.
- Baseline SHA registrado y verificado.

---

## Estado Actual (post Phase 1 audit — 2026-05-04)

| Métrica | Valor |
|---------|-------|
| Baseline SHA | `86739d27` |
| Branches remotas (total) | 31 (incluyendo origin/main) |
| Branches no-main | 30 |
| Fully merged (SAFE_DELETE) | 4 |
| Squash-merged (SAFE_ARCHIVE — requiere archive antes de delete) | 7 |
| Closed-PR sin merge (DO_NOT_DELETE) | 6 |
| Dependabot PRs abiertos | 10 |
| Orphan branches (MANUAL_REVIEW) | 2 (`codex/wo-frictionless-closeout`, `feat/e-v1-daemon-run`) |
| Copilot draft PR | 1 |
| Stash | 1 (patch ~100MB, preservación mínima) |
| Tags existentes | 3 |
| Author identities | 3 (misma persona, .mailmap pendiente) |
| Ghost config entries | 9 (18 líneas) |
| Working tree | ⚠️ SUCIO en main — requiere branch dedicada para hygiene/ |

---

## Fase 0: Protección y Preservación (Riesgo: CERO)

Antes de tocar NADA, creamos puntos de restauración y preservamos el stash como branch real.

### 0.1 — Crear branch de auditoría (con working tree sucio)

⚠️ El working tree en main tiene cambios no commiteados. No usamos `git checkout main` directamente.
En su lugar, creamos la branch desde origin/main y solo commiteamos hygiene/.

```bash
# Crear branch de auditoría desde origin/main (no tocamos working tree sucio)
git checkout -b hygiene/git-audit-20260504 origin/main

# Agregar SOLO los archivos de auditoría (add selectivo)
git add hygiene/preflight-20260504.md \
        hygiene/sha-registry-20260504.md \
        hygiene/branch-audit-20260504.md \
        hygiene/stash-audit-20260504.md \
        hygiene/stash-20260504.patch \
        hygiene/ghost-entries-backup-20260504.txt \
        hygiene/ghost-cleanup-plan-20260504.md \
        hygiene/summary-20260504.md

git commit -m "chore: record git hygiene audit artifacts"
git push -u origin hygiene/git-audit-20260504
```

**Esperado**: Branch creada y pusheada con los 8 archivos de auditoría.
**Rollback**: No aplica — esto es un snapshot aditivo.
**Verificar**: `git log -1 --oneline` muestra el commit.

### 0.2 — Preservar stash como branch remota (NO como patch solamente)

El patch es preservación mínima. Necesitamos branch/commit permanente.

```bash
# Crear branch desde origin/main para el stash
git checkout -b hygiene/stash-preserve-codex-freeze origin/main

# Aplicar el patch del stash
git apply --3way hygiene/stash-20260504.patch

# Verificar que tiene los 22 archivos
git status --short

# Commitear
git add -A
git commit -m "chore: preserve codex freeze stash (123K+ lines, 22 files)"
git push -u origin hygiene/stash-preserve-codex-freeze
```

**Esperado**: Branch remota `hygiene/stash-preserve-codex-freeze` con todo el contenido del stash.
**Rollback**: No aplica — solo adición.
**Verificar**: `git branch -r | grep stash-preserve` y `git log -1 --stat`.

⚠️ **NO ejecutar `git stash drop` hasta confirmar que la branch remota tiene todo el contenido.**
⚠️ **NO mezclar el stash con el working tree sucio de main.**

---

## Fase 1: Documentación (Riesgo: CERO)

Acciones que NO modifican git state. Solo crean archivos.

### 1.1 — Crear `.mailmap`

```bash
# Crear archivo .mailmap en la raíz del repo
cat > .mailmap << 'EOF'
Felipe Gonzalez <felipe.gonzalez@users.noreply.github.com> Felipe Gonzalez Meriño <felipe_gonzalez@MacBook-Pro-de-Felipe.local>
Felipe Gonzalez <felipe.gonzalez@users.noreply.github.com> Felipe <fegome.90@gmail.com>
EOF

# Verificar que unifica las identidades
git shortlog -se | head -5
```

**Esperado**: Las 3 identidades se unifican bajo `Felipe Gonzalez <felipe.gonzalez@users.noreply.github.com>`.
**Rollback**: `rm .mailmap`
**Verificar**: `git shortlog -se` muestra ~740 commits bajo una sola identidad en vez de 3 separadas.

### 1.2 — Commitear .mailmap

```bash
git add .mailmap
git commit -m "docs: add .mailmap to unify author identities"
```

**Esperado**: Commit creado.
**Rollback**: `git revert HEAD`

---

## Fase 2: Cleanup de configuración (Riesgo: MUY BAJO)

Acciones que limpian metadata local. No afectan código ni branches remotas.

### 2.1 — Registrar estado actual de ghost entries

```bash
# Documentar las 9 ghost entries ANTES de limpiar
git config --local --list | grep 'branch\.' > hygiene/ghost-entries-backup-20260504.txt
cat hygiene/ghost-entries-backup-20260504.txt
```

**Esperado**: Archivo con las 9 entries actuales.
**Rollback**: Restaurar desde el backup.

### 2.2 — Limpiar ghost branch tracking entries

```bash
# Eliminar las 9 ghost entries una por una
git config --local --remove-section branch.feat/wo-WO-0011 2>/dev/null
git config --local --remove-section branch.codex/chore-wo-hygiene 2>/dev/null
git config --local --remove-section branch.codex/ci-main-unblock 2>/dev/null
git config --local --remove-section branch.codex/wo-hygiene-rebase 2>/dev/null
git config --local --remove-section branch.codex/wo-guard-wave1 2>/dev/null
git config --local --remove-section branch.codex/wo-take-immediate-validation 2>/dev/null
git config --local --remove-section branch.codex/chore-wo-hygiene-safe 2>/dev/null
git config --local --remove-section branch.codex/merge-trifecta-wo-sidecar-hardening 2>/dev/null
git config --local --remove-section branch.codex/main-consolidation 2>/dev/null

# Verificar
git config --local --list | grep 'branch\.' | wc -l
```

**Esperado**: Solo queda la entry de `main` (o ninguna si no tiene tracking local).
**Rollback**: `cat hygiene/ghost-entries-backup-20260504.txt` y restaurar cada entry con `git config --local --add`.
**Verificar**: `git config --local --list | grep 'branch\.'` solo muestra `main` o nada.

### 2.3 — Verificar hook execution path

```bash
# Confirmar cuál hook path está activo
git config --local core.hookspath

# Verificar qué hooks existen en cada ubicación
ls -la .git/hooks/pre-commit 2>/dev/null && echo "EXISTS in .git/hooks"
ls -la scripts/hooks/pre-commit 2>/dev/null && echo "EXISTS in scripts/hooks"

# Si core.hookspath=scripts/hooks, verificar que funciona
bash -n scripts/hooks/pre-commit && echo "SYNTAX OK"
```

**Esperado**: Claridad sobre cuál hook se ejecuta.
**Acción si hay disconnect**: Documentar finding. No cambiar hooks en esta fase — es una mejora (Tier 3).

---

## Fase 3: Branches Safe Delete (Riesgo: BAJO — código SÍ en main)

Solo las 4 branches que están **fully merged** en main. Código 100% preservado.

### 3.1 — Verificar que son ancestros de main (PREREQUISITO)

```bash
# Para cada branch, confirmar que su tip es ancestor de main
for branch in \
  origin/feat/documentation-skill-phase1 \
  origin/fegome90-cmd/wo-skills-system \
  origin/job/WO-0042 \
  origin/job/WO-0052; do
  echo -n "$branch: "
  if git merge-base --is-ancestor "$branch" main 2>/dev/null; then
    echo "✅ FULLY MERGED — safe to delete"
  else
    echo "⚠️  NOT fully merged — DO NOT DELETE, move to investigation"
  fi
done
```

**Esperado**: Las 4 dicen "✅ FULLY MERGED".
**⚠️ Si alguna dice "NOT fully merged"**: NO borrar. Mover a Fase 5.

### 3.2 — Registrar SHAs antes de borrar (PREREQUISITO)

```bash
# Registrar tip SHA de cada branch ANTES de cualquier deletion
echo "=== SHA RECORDING $(date) ===" > hygiene/sha-registry-20260504.md
for branch in \
  feat/documentation-skill-phase1 \
  fegome90-cmd/wo-skills-system \
  job/WO-0042 \
  job/WO-0052; do
  sha=$(git rev-parse "origin/$branch" 2>/dev/null)
  echo "$branch=$sha" >> hygiene/sha-registry-20260504.md
  echo "Recorded: $branch → $sha"
done
cat hygiene/sha-registry-20260504.md
```

**Esperado**: Archivo con 4 entries `branch=sha`.
**⚠️ CRÍTICO**: Este archivo ES el rollback. No perderlo.

### 3.3 — Eliminar branches remotas

```bash
# Una por una, con verificación posterior
git push origin --delete feat/documentation-skill-phase1
# Verificar: git branch -r | grep feat/documentation-skill-phase1 → no output

git push origin --delete fegome90-cmd/wo-skills-system
# Verificar: git branch -r | grep fegome90-cmd/wo-skills-system → no output

git push origin --delete job/WO-0042
# Verificar: git branch -r | grep job/WO-0042 → no output

git push origin --delete job/WO-0052
# Verificar: git branch -r | grep job/WO-0052 → no output
```

**Esperado**: 4 branches eliminadas del remote.
**Rollback**: `git push origin {sha}:refs/heads/{branch}` usando los SHAs de `hygiene/sha-registry-20260504.md`.
**Verificar**: `git branch -r | wc -l` → debería ser 27 (eran 31).

---

## Fase 4: Branches Squash-Merged (Riesgo: MEDIO — código en main, historial no)

⚠️ **v1.2 CORRECCIÓN**: No hacer delete directo. Primero archivar como `archive/*` remoto, verificar, y solo después delete del nombre original.

Las 7 branches donde el código SÍ llegó a main via squash merge, pero los commits originales NO son ancestors de main. La evidencia de git cherry muestra diffs grandes — la conclusión de "contenido en main" depende de GitHub PR state, no de equivalencia local probada.

| Branch | PR # | PR Merged | Tip SHA |
|--------|------|-----------|---------|
| `codex/skill-hub-ssot-rebuild` | #103 | 2026-04-15 | `796b5a50` |
| `codex/skill-hub-authority-anchor-closeout` | #86 | 2026-04-12 | `abb02938` |
| `codex/graph-mvp` | #74 | 2026-03-15 | `ef56233c` |
| `feat/wo-WO-0042` | #42 | 2026-02-15 | `f065927d` |
| `feat/wo-WO-0044` | #43 | 2026-02-15 | `e62b6a0b` |
| `feat/wo-WO-0047` | #41 | 2026-02-15 | `2fcc80cd` |
| `fix/wo-0055-code-review-issues` | #64,#61,#60,#56 | 2026-02-22 | `7cb317c1` |

### 4.1 — Confirmar squash merge con GitHub

```bash
gh pr view 103 --json state,mergedAt --jq '.state + " " + .mergedAt'
gh pr view 86 --json state,mergedAt --jq '.state + " " + .mergedAt'
gh pr view 74 --json state,mergedAt --jq '.state + " " + .mergedAt'
gh pr view 42 --json state,mergedAt --jq '.state + " " + .mergedAt'
gh pr view 43 --json state,mergedAt --jq '.state + " " + .mergedAt'
gh pr view 41 --json state,mergedAt --jq '.state + " " + .mergedAt'
gh pr view 64 --json state,mergedAt --jq '.state + " " + .mergedAt'
```

**Esperado**: `MERGED` con fecha para las 7.
**⚠️ Si alguna dice `CLOSED`**: NO es squash merge — es closed sin merge. Mover a Fase 5.

### 4.2 — Archivar como branches remotas archive/* (ANTES de cualquier delete)

```bash
# Archivar cada branch como archive/<name>-20260504
for branch in \
  codex/skill-hub-ssot-rebuild \
  codex/skill-hub-authority-anchor-closeout \
  codex/graph-mvp \
  feat/wo-WO-0042 \
  feat/wo-WO-0044 \
  feat/wo-WO-0047 \
  fix/wo-0055-code-review-issues; do
  echo "Archiving $branch..."
  git push origin "refs/remotes/origin/$branch:refs/heads/archive/$branch-20260504"
done
```

**Esperado**: 7 branches `archive/*` creadas en remote.

### 4.3 — Verificar que los archives existen

```bash
# Verificar CADA archive branch
for branch in \
  codex/skill-hub-ssot-rebuild \
  codex/skill-hub-authority-anchor-closeout \
  codex/graph-mvp \
  feat/wo-WO-0042 \
  feat/wo-WO-0044 \
  feat/wo-WO-0047 \
  fix/wo-0055-code-review-issues; do
  echo -n "archive/$branch-20260504: "
  git rev-parse "origin/archive/$branch-20260504" 2>/dev/null && echo "✅ EXISTS" || echo "❌ MISSING"
done
```

**⚠️ CRÍTICO**: Si alguna dice MISSING, NO borrar el nombre original. Investigar primero.

### 4.4 — Solo después de verificar: eliminar nombres originales

```bash
# ⚠️ Solo ejecutar DESPUÉS de verificar que los archives existen
git push origin --delete codex/skill-hub-ssot-rebuild
git push origin --delete codex/skill-hub-authority-anchor-closeout
git push origin --delete codex/graph-mvp
git push origin --delete feat/wo-WO-0042
git push origin --delete feat/wo-WO-0044
git push origin --delete feat/wo-WO-0047
git push origin --delete fix/wo-0055-code-review-issues
git fetch --prune
```

**Rollback**: Las branches `archive/*` preservan todo. Restaurar con:
```bash
git push origin "refs/remotes/origin/archive/$branch-20260504:refs/heads/$branch"
```

---

## Fase 5: Branches Closed-PR sin Merge (Riesgo: ALTO — código NO en main)

⚠️ **Estas 6 branches tienen commits que NUNCA llegaron a main.** Borrarlas pierde trabajo.

| Branch | Commits únicos | PR | Estado |
|--------|---------------|-----|--------|
| `fix/search-context-preview-truncation` | ~36 | #83 | CLOSED |
| `codex/batch-2d-runtime-manager` | ~38 | #81 | CLOSED |
| `codex/docs-skillhub-context-refresh-20260327` | ~33 | #80 | CLOSED |
| `codex/wo-remediation-ci-baseline` | ~12 | #78 | CLOSED |
| `feat/skills-contracts-explain` | ~14 | #68 | CLOSED |
| `fegome90-cmd/wo-0015-work` | ~16 | #66 | CLOSED |

### 5.1 — Confirmar que el código NO está en main

```bash
for branch in \
  fix/search-context-preview-truncation \
  codex/batch-2d-runtime-manager \
  codex/docs-skillhub-context-refresh-20260327 \
  codex/wo-remediation-ci-baseline \
  feat/skills-contracts-explain; do
  echo "=== $branch ==="
  commits=$(git log main.."origin/$branch" --oneline 2>/dev/null | wc -l)
  echo "$commits commits NOT in main"
  files=$(git diff main..."origin/$branch" --stat 2>/dev/null | tail -1)
  echo "Diff: $files"
  echo ""
done
```

**Esperado**: Cada branch muestra commits y diffs significativos.
**⚠️ Esto confirma que BORRAR = PERDER CÓDIGO.**

### 5.2 — DECISIÓN REQUERIDA — Por cada branch

Para cada una de las 5 branches, elegir una de estas opciones:

**Opción A: Preservar como tag (recomendado si hay duda)**
```bash
# Ejemplo para una branch
sha=$(git rev-parse "origin/$branch")
git tag "preserve/$branch-$(date +%Y%m%d)" "$sha"
git push origin "preserve/$branch-$(date +%Y%m%d)"
# Luego: git push origin --delete $branch
```

**Opción B: Aplicar a una branch de feature (si el trabajo es valioso)**
```bash
git checkout -b "recover/$branch" "origin/$branch"
git push origin "recover/$branch"
# Luego: git push origin --delete $branch
```

**Opción C: Confirmar eliminación (solo si estás 100% seguro que el trabajo es descartable)**
```bash
# ⚠️ NO HAY VOLVER ATRÁS después de gc
sha=$(git rev-parse "origin/$branch")
echo "DELETING $branch (sha: $sha) — code NOT in main" 
# git push origin --delete $branch
```

⚠️ **NO ejecutar Opción C sin confirmación explícita branch por branch.**

---

## Fase 6: Dependabot PRs (Riesgo: BAJO-MEDIO)

10 PRs de actualización de dependencias, 3 semanas stale.

### 6.1 — Listar y priorizar

```bash
gh pr list --state open --author "app/dependabot" --json number,title,createdAt --jq '.[] | "\(.number) \(.title)"'
```

### 6.2 — Merge seguro (priorizar security updates)

```bash
# Seguridad primero — estos son los más urgentes
gh pr merge 94 --squash  # safety >=3.7.0

# Luego las que no rompen APIs
gh pr merge 95 --squash  # types-pyyaml
gh pr merge 96 --squash  # mypy
gh pr merge 97 --squash  # filelock

# Las que pueden tener breaking changes — revisar primero
# gh pr view 98 --json title,body  # tree-sitter — verificar compatibilidad
# gh pr view 99 --json title,body  # ruamel-yaml — verificar compatibilidad
# gh pr view 100 --json title,body # plotly — verificar compatibilidad
# gh pr view 101 --json title,body # pytest-env — verificar compatibilidad
# gh pr view 102 --json title,body # pandas — verificar compatibilidad
# gh pr view 93 --json title,body  # typer — CLI framework, VERIFICAR antes
```

**Regla**: Si un PR tiene conflictos o breaking changes, cerrarlo y dejar que dependabot regenere.
**Verificar**: `uv run pytest -m "not slow"` después de cada merge.

### 6.3 — Cleanup de branches dependabot

```bash
# Las branches se limpian automáticamente al mergear via GitHub
# Verificar branches restantes
git fetch --prune
git branch -r | grep dependabot
```

---

## Fase 7: Orphan Branches (Riesgo: VARIABLE — requiere investigación)

⚠️ **v1.2 CORRECCIÓN**: Solo 2 branches son true orphans (sin PR). Las otras 5 (feat/wo-WO-0042, feat/wo-WO-0044, feat/wo-WO-0047, fix/wo-0055-code-review-issues, fegome90-cmd/wo-0015-work) fueron reclasificadas: las primeras 4 son squash-merged (Fase 4), la última es closed-PR (Fase 5).

| Branch | Commits | Archivos | Último commit |
|--------|---------|----------|---------------|
| `codex/wo-frictionless-closeout` | 16 | 347 | 2026-03-19 |
| `feat/e-v1-daemon-run` | 1 | 528 | 2026-03-06 |

### 7.1 — Investigar cada branch

```bash
for branch in \
  codex/wo-frictionless-closeout \
  feat/e-v1-daemon-run; do
  echo "=== $branch ==="
  echo "Last commit: $(git log -1 --format='%ci' origin/$branch 2>/dev/null)"
  echo "Commits: $(git log main..origin/$branch --oneline 2>/dev/null | wc -l)"
  echo "Diff files: $(git diff main...origin/$branch --stat 2>/dev/null | tail -1)"
  echo ""
done
```

### 7.2 — DECISIÓN REQUERIDA — Por cada branch

Mismo menú que Fase 5: tag (preservar) / branch de recovery / delete confirmado.

---

## Fase 8: Copilot PR + Branch (Riesgo: BAJO)

### 8.1 — Cerrar PR #85

```bash
gh pr close 85 --comment "Closing stale draft PR. Branch audit data preserved if needed."
```

### 8.2 — Registrar SHA y eliminar branch

```bash
sha=$(git rev-parse "origin/copilot-pull-request-reviewer/audit-github-history")
echo "copilot-reviewer=$sha" >> hygiene/sha-registry-20260504.md

# Preservar como tag
git tag "archive/copilot-audit-$(date +%Y%m%d)" "$sha"
git push origin --tags

# Eliminar branch
git push origin --delete copilot-pull-request-reviewer/audit-github-history
```

---

## Fase 9: Stash (Riesgo: ALTO — ya preservado en Fase 0)

### 9.1 — Confirmar que la branch de preservación tiene todo

```bash
# Verificar la branch creada en paso 0.2
git log hygiene/stash-preserve-codex-freeze --oneline | head -5
git diff hygiene/stash-preserve-codex-freeze --stat | tail -3
```

**Esperado**: La branch tiene todos los 22 files del stash original.

### 9.2 — DECISIÓN REQUERIDA

**Opción A**: Pushear la branch al remote como referencia permanente
```bash
git push origin hygiene/stash-preserve-codex-freeze
```

**Opción B**: Documentar como frozen y dropear el stash local
```bash
# ⚠️ Solo después de confirmar Opción A
git stash drop stash@{0}
```

**⚠️ NO dropear el stash hasta confirmar que la branch remota tiene todo.**

---

## Fase 10: Mejoras (Riesgo: CERO)

### 10.1 — Agregar labels a issues

```bash
# Categorizar los 6 issues abiertos
gh issue edit 87 --add-label "bug,skill-hub" 
gh issue edit 88 --add-label "bug,skill-hub"
gh issue edit 89 --add-label "bug,daemon"
gh issue edit 90 --add-label "bug,lsp"
gh issue edit 91 --add-label "bug,lsp"
gh issue edit 92 --add-label "bug,skill-hub"
```

### 10.2 — Limpiar branch de seguridad (opcional, al final)

```bash
# Solo si TODO salió bien y ya no necesitamos el snapshot
git push origin --delete hygiene/safety-snapshot-20260504
```

---

## Verificación Final

```bash
echo "=== POST-HYGIENE VERIFICATION ==="
echo ""
echo "Remote branches remaining:"
git branch -r | grep -v HEAD | wc -l
echo "(Expected: ~17 = main + safety + stash-preserve + dependabot remaining + orphan remaining)"
echo ""
echo "Author identity unified:"
git shortlog -se | head -3
echo "(Expected: Felipe Gonzalez as primary author)"
echo ""
echo "Stash list:"
git stash list
echo "(Expected: empty after Fase 9)"
echo ""
echo "Ghost config entries:"
git config --local --list | grep 'branch\.' | grep -v 'main' | wc -l
echo "(Expected: 0)"
echo ""
echo "Tags created:"
git tag -l | grep -E "^(archive|preserve|hygiene)"
echo "(Expected: tags from Fases 4-5-8)"
echo ""
echo "Open PRs:"
gh pr list --state open --json number --jq 'length'
echo "(Expected: fewer than 11)"
```

---

## Orden de ejecución (v1.2 — corregido post-veredicto)

```
Fase 0 (Protección + Stash preserve) → PRIMERO, siempre
  ├── 0.1 Branch de auditoría (commit hygiene/ en branch dedicada)
  └── 0.2 Stash → branch remota (NO patch solamente)
Fase 1 (Documentación: .mailmap)    → Sin riesgo
Fase 2 (Config cleanup: ghost)      → Solo local
Fase 3 (Safe deletes: 4 fully merged) → Código preservado en main
Fase 4 (Archive squash-merged: 7)   → archive/* PRIMERO, verificar, DESPUÉS delete
Fase 5 (Closed-PR: 6) ⚠️           → REQUIERE DECISIÓN por branch
Fase 6 (Dependabot) ⚠️             → Requiere working tree limpio + tests
Fase 7 (Orphans: 2) ⚠️             → REQUIERE INVESTIGACIÓN
Fase 8 (Copilot)                    → Simple cleanup
Fase 9 (Stash drop) ⚠️             → Solo después de Fase 0.2 verificada
Fase 10 (Mejoras)                   → Cierre
```

### Lo que se puede ejecutar AHORA (bajo riesgo):

1. ✅ Commitear hygiene/ en branch dedicada
2. ✅ Preservar stash como branch remota
3. ✅ Limpiar ghost config (9 entries, local-only)
4. ✅ Crear .mailmap
5. ✅ Borrar 4 fully merged
6. ✅ Archivar 7 squash-merged (archive/* primero)

### Lo que queda BLOQUEADO (requiere decisión):

- Fase 4.4: Delete nombres originales squash-merged (solo después de verificar archive/*)
- Fase 5: Closed-PR branches (revisión semántica branch-by-branch)
- Fase 6: Dependabot (working tree sucio, requiere tests)
- Fase 7: Orphans (investigación de contenido)
- Fase 9: Stash drop (solo después de verificar branch remota)

---

## Rollback general

Si algo sale mal en cualquier punto:

```bash
# Restaurar branch desde SHA registry
cat hygiene/sha-registry-20260504.md
git push origin {sha}:refs/heads/{branch-name}

# Restaurar config desde backup
cat hygiene/ghost-entries-backup-20260504.txt

# Restaurar stash desde branch de preservación
git checkout hygiene/stash-preserve-codex-freeze
```
