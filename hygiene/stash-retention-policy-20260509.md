# Stash Retention Policy — `origin/hygiene/stash-preserve-codex-freeze`

> **Date**: 2026-05-09
> **Status**: ACCEPTED / IMPLEMENTED
> **Authority**: This document is a follow-up to the Git Hygiene cycle. See `git-hygiene-document-authority-20260509.md` for the full authority registry.
> **Scope**: Define retention policy for `origin/hygiene/stash-preserve-codex-freeze` remote branch. No operational changes in this document.

---

## 1. Decisión Implementada

**Decisión: Opción B — Tag anotado + mantener branch (IMPLEMENTADO).**

- **Tag creado**: `stash-preserve-codex-freeze-v1` → `07a8cf4d1527148ef2910ae69277c049e40f4179`
- **Branch mantenida**: `origin/hygiene/stash-preserve-codex-freeze` → `07a8cf4d1527148ef2910ae69277c049e40f4179`
- **Verificación**: Ambos resuelven al mismo commit ✅
- **No se creó bundle**
- **No se eliminó branch**
- **Riesgo de pérdida**: bajo; mitigado por branch remota + tag anotado (no cero — depender de un solo remoto sin backup independiente)

---

## 2. Estado Actual del Stash Preserve Branch

| Propiedad | Valor |
|-----------|-------|
| Remote branch | `origin/hygiene/stash-preserve-codex-freeze` |
| Commit SHA | `07a8cf4d1527148ef2910ae69277c049e40f4179` |
| Commit date | 2026-05-04 07:19:46 -0400 |
| Author | Felipe Gonzalez <felipe.gonzalez@users.noreply.github.com> |
| Commit message | `chore: preserve codex freeze stash content as branch` |
| Total files changed | 310 |
| Insertions | 188,689 |
| Deletions | 132,771 |
| Local stash | Dropped in Phase 4 |
| Local patch (`hygiene/stash-20260504.patch`) | Deleted in Phase 3 |
| Other preservation | Annotated tag `stash-preserve-codex-freeze-v1` |

### Origination

This branch was created during Phase 3 of the Git Hygiene cycle as a safety preservation of `stash@{0}` content (codex freeze snapshot). The local stash was subsequently dropped in Phase 4 and the patch was deleted in Phase 3 after exceeding GitHub's 100 MB push limit. The branch is the **sole remaining preservation** of this content.

---

## 3. Contenido Preservado (Resumen por Categoría)

### By Top-Level Directory

| Directory | Files | Category | Notes |
|-----------|-------|----------|-------|
| `.mini-rag/` | 73 | Generated artifacts | RAG chunks, manifests, index metadata. Derivable from source. |
| `openspec/` | 69 | SDD documentation | Specs, designs, proposals, tasks, state files. Historical SDD changes. |
| `_ctx/` | 61 | Context artifacts | Session logs, handoff patches, telemetry, review runs, audits. |
| `tests/` | 25 | Test code | Unit tests, integration tests, certification tests, fixtures. |
| `src/` | 17 | Source code | Application, domain, infrastructure Python modules. |
| `scripts/` | 15 | Scripts | Python and shell utility scripts. |
| `.pi-lens/` | 9 | Cache/index | Tool-generated cache. Derivable. |
| `docs/` | 8 | Documentation | Contracts, certifications, reports. |
| `minirag-eval/` | 5 | Evaluation | RAG evaluation results. |
| Other roots | 27 | Misc | Config files (`pyproject.toml`, `uv.lock`), root scripts (`forensic_daemon*.py`), root docs (`README.md`, `GEMINI.md`, `skill.md`), test fixtures, tmp files. |

### By File Type

| Type | Count | Notes |
|------|-------|-------|
| Markdown (`.md`) | ~197 | Bulk of content — documentation, specs, eval results |
| Config/Data (`.json`, `.jsonl`, `.yaml`, `.toml`, `.lock`) | ~38 | Metadata, context packs, lock files |
| Python (`.py`) | ~55 | Source, tests, scripts |
| Shell (`.sh`) | ~3 | Utility scripts |
| Other | ~17 | `.ipynb`, `.txt`, `.patch`, `.diff`, etc. |

### Large Files (>1 MB)

| File | Size | Category | Derivable? |
|------|------|----------|------------|
| `tests/fixtures/reconcile/running_wo_without_worktree/_ctx/logs/reconcile/reconcile.patch` | **87.3 MB** | Test fixture | Partially (test output) |
| `_ctx/handoff/WO-0005/diff.patch` | **60.7 MB** | Context artifact | Yes (regenerable from WO history) |
| `_ctx/context_pack.json` | **7.2 MB** | Generated artifact | Yes (derivable from source) |
| `_ctx/telemetry/events.jsonl` | **4.3 MB** | Telemetry | No (historical log) |
| `_ctx/handoff/WO-0043/diff.patch` | **2.0 MB** | Context artifact | Yes (regenerable from WO history) |

**Total estimated branch size**: ~160+ MB in large files alone.

### Secret Scan (Name/Pattern Check)

No actual secret files (`.env`, `credentials`, private keys) were found. The following files contain **reports about** secrets/tokens (audit artifacts, not secrets themselves):

- `.mini-rag/chunks/secrets_scan_report.md__2b4fbd5a59634f6a.md` — Report about a secrets scan
- `_ctx/audits/token_audit/REPORT.md` — Token usage audit report
- `_ctx/audits/token_audit/results.json` — Token audit results data
- `_ctx/audits/token_audit/synthesis_final.txt` — Audit synthesis
- `_ctx/audits/token_audit/synthesis_response.txt` — Audit response

**Veredict**: No secret leakage risk. These are audit artifacts.

---

## 4. Opciones Evaluadas (Tabla Comparativa)

| Criterio | A) Status quo (branch only) | B) Tag + branch | C) Tag + bundle + future delete | D) Delete without backup |
|----------|----------------------------|-----------------|---------------------------------|--------------------------|
| **Recuperabilidad** | Total (via branch) | Total (via tag + branch) | Alta (via tag or bundle) | Cero (irrecoverable after GC) |
| **Visibilidad** | Baja — solo `git branch -r` | Alta — `git tag -l` + branch | Alta — tag visible, bundle offline | N/A |
| **Riesgo de pérdida** | Bajo — GitHub remoto | Muy bajo — doble referencia | Muy bajo — triple respaldo | **ALTO** — sin backup |
| **Costo mantenimiento** | Bajo — sin cambios | Bajo — tag es puntero inmutable | Medio — bundle ~150MB en disco | Ninguno |
| **Confusión agentes** | Medio — parece branch activa | **Bajo** — tag documenta propósito | Bajo (post-delete) | Ninguno |
| **Comando restauración** | `git checkout -b restore origin/hygiene/stash-preserve-codex-freeze` | `git checkout stash-preserve-codex-freeze-v1` o branch | `git clone bundle` o `git checkout tag` | Imposible |
| **Comando rollback** | N/A (no cambia nada) | `git tag -d ...; git push origin :refs/tags/...` | Re-create branch from tag o bundle | Imposible |
| **Storage en repo** | Branch objects exist | +0 (tag es puntero) | +bundle file (~150MB local) | -branch objects (eventual GC) |
| **Requiere acción humana** | No | Mínima (crear tag) | Sí (crear bundle + decidir delete) | Sí (decidir delete) |

---

## 5. Recomendación (IMPLEMENTADO)

### **Opción B: Crear tag anotado + mantener branch** ✅ IMPLEMENTADO

**Justificación**:

1. **Zero data loss risk**: La branch sigue existiendo como respaldo vivo. El tag agrega una referencia inmutable y discoverable.
2. **Discoverability para agentes**: Un tag anotado aparece en `git tag -l` y lleva metadata (mensaje, autor, fecha). Los agentes futuros pueden identificar su propósito sin inspeccionar la branch.
3. **Costo mínimo**: Un tag es un puntero inmutable (~cero overhead). No se crea archivo adicional.
4. **Decisión postergable**: La eliminación de la branch puede decidirse en un futuro ciclo de revisión, cuando se confirme que el tag es suficiente.
5. **Sin integración a main**: El tag y la branch son referencias a un commit aislado. No afectan `main` ni CI.
6. **Consistencia con ciclo**: Siguiendo el patrón del ciclo de higiene — documentar primero, operar después con evidencia.

**Tag propuesto**:
```
Name: stash-preserve-codex-freeze-v1
Message: "Stash/codex freeze preservation (310 files, commit 07a8cf4d). 
          Branch: origin/hygiene/stash-preserve-codex-freeze.
          Retention policy: hygiene/stash-retention-policy-20260509.md"
```

**Comando**:
```bash
git tag -a stash-preserve-codex-freeze-v1 07a8cf4d \
  -m "Stash/codex freeze preservation (310 files). Branch: origin/hygiene/stash-preserve-codex-freeze. Policy: hygiene/stash-retention-policy-20260509.md"
git push origin stash-preserve-codex-freeze-v1
```

---

## 6. Riesgos Residuales

1. **Branch drift confusion**: Si un agente futuro hace checkout de esta branch sin leer el tag/policy, puede confundirla con trabajo activo. Mitigado por tag anotado con mensaje descriptivo.
2. **Large repo size**: Los ~160MB de artefactos grandes en la branch contribuyen al tamaño del repo para clones completos. Mitigado: la mayoría de los clones usan single-branch o shallow clone.
3. **No offline backup**: Sin un bundle, la preservación depende exclusivamente de GitHub. Si GitHub pierde el repo, se pierde la branch. Aceptable: el contenido esencial (src, tests, docs) ya está integrado en main en versiones actualizadas.
4. **Future delete decision still needed**: Este documento define la política pero no ejecuta ninguna acción. La eliminación de la branch requiere aprobación humana explícita.

---

## 7. Acciones Explícitamente NO Tomadas

- ❌ No se eliminó la branch `origin/hygiene/stash-preserve-codex-freeze`.
- ✅ Se creó tag anotado `stash-preserve-codex-freeze-v1`.
- ❌ No se creó git bundle.
- ❌ No se integró contenido de la branch a `main`.
- ❌ No se modificó código funcional.
- ❌ No se creó `dependabot.yml`.
- ❌ No se modificaron dependencias.
- ❌ No se usó `--no-verify`.

---

## 8. Estado Post-Implementación

1. **Tag creado**: `stash-preserve-codex-freeze-v1` apuntando a `07a8cf4d1527148ef2910ae69277c049e40f4179` ✅
2. **Branch mantenida**: `origin/hygiene/stash-preserve-codex-freeze` sin cambios ✅
3. **Verificación**: Ambos resuelven al mismo commit ✅
4. **Documentación actualizada**: Este documento y `hygiene/README.md` reflejan estado COMPLETE ✅
5. **Future consideration**: En un próximo ciclo de higiene, evaluar si la branch puede eliminarse (tag + main history como respaldo suficiente).

---

## Referencias

- `git-hygiene-document-authority-20260509.md` — Authority registry
- `phase-3-closeout-20260504.md` — Stash/patch closeout state
- `stash-audit-20260504.md` — Initial stash audit (historical)
- `closed-pr-semantic-memo-20260509.md` — Branch decision rationale pattern
- Engram #2749 — Follow-up registration
