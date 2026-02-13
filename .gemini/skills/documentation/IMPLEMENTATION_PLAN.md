# Agent Documentation Skill - Implementation Plan

**Last Updated**: 2026-02-10  
**Status**: READY FOR EXECUTION  
**Based On**: ECC (Everything Claude Code) workflow analysis

---

## 📋 Executive Summary

Mejora la **Agent Documentation Skill** adoptando patrones de ECC:
- Crear **llms.txt** optimizado para agentes
- Implementar **validación cruzada de referencias** avanzada
- Agregar **contextos inyectables dinámicos** (dev/review/research)
- Crear **guías bifurcadas** (QUICKSTART + ADVANCED)
- Implementar **Git Hook automation** (pre-commit + ctx sync)

**Objetivo Final**: Docs siempre sincronizados, validados pre-commit, actualizados automáticamente.

---

## 🎯 Visión General

### Antes (Estado Actual)
```
Code Change → Manual doc update → Manual validation → Manual PR
```

### Después (Con Mejoras)
```
Code Change → Auto doc-skill → Auto validate → Auto ctx sync → PR Ready
           ↑
         Git Hook (Pre-Commit)
```

---

## 📊 Fases de Implementación

### **FASE 1: Core Improvements** ⭐ (QUICK WINS)

**Duración Estimada**: 2-3 horas  
**Prioridad**: 🔴 ALTA (foundation)

#### 1.1 Crear `llms.txt` - Documentación optimizada para agentes

**Propósito**: Versión limpia de configuración sin ruido visual

**Contenido**:
```
Quick Reference
  ├─ Commands principales
  ├─ Ubicaciones clave
  └─ Setup inicial

Configuración Actual
  ├─ CLAUDE.md structure
  ├─ Reglas del proyecto
  └─ Agents disponibles

Skill Documentation
  ├─ Ubicaciones de skills
  ├─ Estructura de recursos
  └─ Patrones recomendados

Data Structures
  ├─ _ctx/ directories
  ├─ Work order (WO) schema
  └─ Telemetry format

Troubleshooting
  ├─ Common issues
  ├─ Solution paths
  └─ Escalation procedures
```

**Ubicación**: `/workspaces/trifecta_dope/llms.txt` (in root)  
**Tamaño**: ~120 lines  
**Formato**: Markdown clean (sin emojis, sin visual noise)

---

#### 1.2 Crear `validate-references.sh` - Validación cruzada avanzada

**Propósito**: Mejorar verify_documentation.sh con validación de paths reales

**Nuevas Validaciones**:
- ✅ Paths mencionados en CLAUDE.md/agents.md existen (FAIL)
- ✅ Paths absolutos detectados (FAIL)
- ✅ Secciones CRITICAL están PRIMERO en ambos archivos (FAIL)
- ✅ CLAUDE.md ↔ agents.md sincronizados (mismos archivos obligatorios) (FAIL)
- ⚠️ Timestamps "Last Updated" > 90 días (WARN)
- ⚠️ Links externos no resueltos (WARN)

**Ubicación**: `skills/documentation/resources/validate-references.sh`  
**Type**: Bash wrapper + Python parser (stdlib)

**Features**:
```bash
Exit Codes:
  0 = PASS (todo bien)
  1 = FAIL (bloqueante)
  
Output:
  [✓] PASS: Architecture section found
  [✗] FAIL: Path /Users/... uses absolute path (not relative)
  [⚠] WARN: Last updated 120 days ago (recommend refresh)
  
Summary: 5 PASS, 2 FAIL, 1 WARN
```

---

#### 1.3 Crear `contexts/` folder - Contextos inyectables dinámicos

**Propósito**: Diferentes directrices según modo de actividad

**Estructura**:
```
skills/documentation/resources/contexts/
├── dev.md
│   ├─ Emphasis: Testing, architecture validation
│   ├─ Tools allowed: pytest, mypy, ruff
│   └─ Critical paths: src/domain/, src/tests/
│
├── review.md
│   ├─ Emphasis: Security, performance, patterns
│   ├─ Tools required: mypy, security checkers
│   └─ Auto-check: Architecture violations
│
└── research.md
    ├─ Emphasis: Exploration, documentation
    ├─ Tools: grep, AST analysis, exploration
    └─ Output: Finding summary + evidence
```

**Uso**:
```bash
# Developer uses:
cat skills/documentation/resources/contexts/dev.md >> .claude-context

# During review:
cat skills/documentation/resources/contexts/review.md >> .claude-context
```

---

#### 1.4 Crear Guías Bifurcadas - Onboarding estratificado

**QUICKSTART.md** (5 minutos)
```
├─ What is Trifecta? (1 paragraph)
├─ Setup (3 commands)
├─ First Task (example)
├─ 3 Core Rules
├─ Where to Go Next
└─ Emergency Contacts
```
**Ubicación**: `skills/documentation/resources/guides/QUICKSTART.md`

**ADVANCED.md** (30 minutos)
```
├─ Token optimization patterns
├─ Memory persistence (session.md updates)
├─ Parallel execution (subagent strategies)
├─ Telemetry & observability
├─ Error recovery patterns
├─ Performance profiling
└─ Extending the system
```
**Ubicación**: `skills/documentation/resources/guides/ADVANCED.md`

---

### **FASE 2: Git Hook Integration** 🔗 (AUTOMATION)

**Duración Estimada**: 3-4 horas  
**Prioridad**: 🟠 MEDIA-ALTA (enables automation)

#### 2.1 Crear `install-hooks.sh` - Setup de hooks

**Propósito**: Instalar/actualizar hooks usando `core.hooksPath` (robusto en worktrees)

**Script Logic**:
```bash
#!/bin/bash
# scripts/hooks/install-hooks.sh

# 1. Set hooks path once (works in worktrees too)
git config core.hooksPath scripts/hooks

# 2. Ensure hooks are executable
chmod +x scripts/hooks/pre-commit
chmod +x scripts/hooks/post-commit

echo "✅ Git hooks installed"
```

**Ubicación**: `scripts/hooks/install-hooks.sh` (executable)  
**Integration**: Ejecutar en `make setup` o `uv sync`

---

#### 2.2 Crear `pre-commit` Hook - Main automation

**Propósito**: Ejecutar doc-skill + validate + ctx sync ANTES de commit

**Flujo Detallado**:

```bash
#!/bin/bash
# scripts/hooks/pre-commit

set -e

# Optional kill-switch
if [[ "${TRIFECTA_HOOKS_DISABLE:-0}" == "1" ]]; then
  echo "ℹ️  TRIFECTA_HOOKS_DISABLE=1, skipping hooks"
  exit 0
fi

CHANGED_FILES=$(git diff --cached --name-only)

# Solo ejecutar si hay cambios en código
if ! echo "$CHANGED_FILES" | grep -qE "^src/|^pyproject.toml|^tests/"; then
    echo "ℹ️  No code changes detected, skipping doc update"
    exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Documentation Auto-Update Hook"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# STEP 1: Run doc-skill
echo ""
echo "1️⃣  Running doc-skill (apply updates)..."
bash scripts/hooks/run-doc-skill.sh || {
    echo "❌ Doc-skill failed"
    exit 1
}

# STEP 2: Validate references
echo ""
echo "2️⃣  Validating documentation references..."
bash skills/documentation/resources/validate-references.sh || {
    echo "❌ Validation failed! Fix docs and retry."
    exit 1
}

# STEP 3: Execute ctx sync
echo ""
echo "3️⃣  Syncing context pack (ctx sync)..."
if uv run trifecta ctx sync --segment . > /dev/null 2>&1; then
    echo "✅ Context pack synced"
else
    echo "⚠️  ctx sync had issues (non-blocking, check _ctx/ manually)"
fi

# STEP 4: Auto-stage changes (docs only)
echo ""
echo "4️⃣  Staging documentation changes..."
git add CLAUDE.md agents.md llms.txt skills/documentation/resources/guides/ 2>/dev/null || true
echo "✅ Changes staged"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Ready to commit!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit 0
```

**Ubicación**: `scripts/hooks/pre-commit` (executable)

**Exit Behavior**:
- Exit 0 = Commit allowed
- Exit 1 = Commit blocked (validation failed)
- Warning messages = Non-blocking, user can fix later

---

#### 2.3 Crear `run-doc-skill.sh` - Wrapper para ejecutar skill

**Propósito**: Aplicar actualizaciones de documentación sin ser interactivo ni usar LLM

**Logic**:

```bash
#!/bin/bash
# scripts/hooks/run-doc-skill.sh

CHANGED=$(git diff --cached --name-only)

# Detectar qué cambió
if echo "$CHANGED" | grep -qE "src/domain/|src/application/"; then
    echo "📋 Updating architecture docs..."
    # Comprobar si hay nuevas classes/functions
    # Actualizar ADVANCED.md con nuevos patrones
fi

if echo "$CHANGED" | grep -q "pyproject.toml"; then
    echo "📦 Updated pyproject.toml, refreshing config docs..."
    # Actualizar sección "Configuration" en CLAUDE.md
fi

if echo "$CHANGED" | grep -qE "skills/|agents/"; then
  echo "🤖 Skill/agent changes detected, updating llms.txt..."
  # Regenerate llms.txt from repo tree (deterministic, sorted)
fi

# Add more detections as needed
```

**Ubicación**: `scripts/hooks/run-doc-skill.sh` (executable)

---

#### 2.4 Crear `post-commit` Hook - Sync final (opcional)

**Propósito**: Ejecutar ctx sync DESPUÉS del commit (asíncrono)

```bash
#!/bin/bash
# scripts/hooks/post-commit (optional)

# Solo si está en un worktree
if [[ -f .git/worktreeConfig ]]; then
    # Ejecutar ctx sync en background
    (uv run trifecta ctx sync --segment . &) 2>/dev/null
fi
```

---

#### 2.5 Crear `HOOKS_GUIDE.md` - Documentación

**Propósito**: Guía para entender y usar hooks

**Contenido**:
```
├─ What are git hooks?
├─ Installation (install-hooks.sh)
├─ Hook Chain (pre-commit → post-commit)
├─ Bypass Hooks (--no-verify)
├─ Troubleshooting
└─ Customization
```

**Ubicación**: `skills/documentation/resources/HOOKS_GUIDE.md`

---

### **FASE 3: Update SKILL.md** 📖 (DOCUMENTATION)

**Duración Estimada**: 1 hora  
**Prioridad**: 🟡 BAJA (refactor de existing)

#### 3.1 Actualizar SKILL.md principal

**Cambios**:
```markdown
Agregar sección después de "Common Mistakes":

## Progressive Disclosure Pattern

Diferentes guías por nivel de experiencia:
├─ QUICKSTART (5 min)
├─ ADVANCED (30 min)
└─ Full documentation (reference)

Agregar sección:

## Git Hook Automation

La skill se ejecuta automáticamente vía pre-commit hook:
- Detecta cambios en código
- Ejecuta doc-skill
- Valida referencias
- Ejecuta ctx sync (WARN-only)
- Auto-stages docs (no `_ctx/` por default)

Agregar referencia a:

## Resources Available

- templates/ - Copy-paste ready templates
- validate-references.sh - Validation script
- contexts/ - Inyectable context by mode
- guides/ - QUICKSTART + ADVANCED
- hooks/ - Git hook setup + scripts
- examples/ - Before/after patterns
- workflows/ - Pipeline documentation
```

**Ubicación**: Update existing `/workspaces/trifecta_dope/skills/documentation/SKILL.md`

---

#### 3.2 Actualizar resources/README.md

**Cambios**:
```markdown
Agregar nuevas secciones:

## Progressive Disclosure Workflows

### For New Developers (QUICKSTART path)
1. Read QUICKSTART.md
2. Copy CLAUDE_md_template.md
3. Customize placeholders
4. Run validate-references.sh
5. Commit

### For Advanced Users (ADVANCED path)
1. Read ADVANCED.md
2. Explore contexts/
3. Understand hook automation
4. Extend with custom patterns

## Context Injection

Inject different guidance by mode:
- contexts/dev.md - Development mode
- contexts/review.md - Review mode
- contexts/research.md - Research mode

## Git Hooks

Automated documentation updates:
- See HOOKS_GUIDE.md
- Run scripts/hooks/install-hooks.sh in setup
- Hooks execute on each commit
- Disable with TRIFECTA_HOOKS_DISABLE=1 (if needed)
```

---

## 🔧 Análisis Técnico: Git Hooks

### **Arquitectura de Hooks**

```
git config core.hooksPath scripts/hooks

scripts/
└── hooks/
  ├── install-hooks.sh (setup script)
  ├── pre-commit (main automation)
  ├── run-doc-skill.sh (skill executor)
  ├── post-commit (optional async)
  └── README.md (documentation)
```

### **Opciones Evaluadas**

| Opción | Ventajas | Desventajas | Recomendación |
|--------|----------|------------|---------------|
| **A: Pre-Commit Hook** | Valida temprano, local | Ralentiza commits | ⭐ **USAR** |
| **B: Pre-Push Hook** | Última oportunidad | Muy tardío | COMPLEMENTARIO |
| **C: GitHub Actions** | CI/CD integrado | Requiere PR | COMPLEMENTARIO |
| **D: Hybrid** | Best of both | Más complejo | ⭐ **RECOMENDADO** |

### **Decisión: Implementar Opción D Hybrid**

```
Componente       | Dónde          | Cuándo              | Bloqueante
─────────────────|─────────────────|──────────────────────|───────────
pre-commit hook  | Local worktree  | Antes cada commit    | SÍ (validation)
ctx sync         | Local          | Post-commit (async)  | NO (warning)
GitHub Actions   | CI/CD          | Pre-PR               | Verificación
```

### **Manejo de Errores en ctx sync**

**Problema**: ctx sync puede fallar o ser lento

**Solución**:
```bash
# En pre-commit: No bloqueante
uv run trifecta ctx sync --segment . || {
    echo "⚠️ ctx sync warning (non-blocking)"
}

# En post-commit: Async en background
(uv run trifecta ctx sync --segment . &)
```

---

## ⚠️ Problemas Identificados & Soluciones

### **Problema 1: Hook en Worktree Context**

**Issue**: `.git` es un archivo en worktrees, no un directorio con hooks.

**Solución**: Usar `git config core.hooksPath scripts/hooks` (idempotente, funciona en worktrees).

**Implementación**:
```bash
# En cualquier repo o worktree:
git config core.hooksPath scripts/hooks
```
git commit -m "feat: update docs"
  → hook ejecuta doc-skill + ctx sync
  → cambios staged automáticamente

git push origin feat/wo-WO-XXXX  
  → Sube a origin (incluye docs actualizados)
```

---

### **Problema 2: Frecuencia de Ejecución**

**Issue**: Ejecutar doc-skill en CADA commit puede ser lento

**Soluciones**:
1. ✅ Skip si no hay cambios en src/ (optimización inteligente)
2. ✅ Opción `--no-verify` para bypass urgente: `git commit --no-verify`
3. ✅ Paralelizar (ctx sync en background post-commit)

**Implementación**:
```bash
# En pre-commit, detectar:
if ! git diff --cached --name-only | grep -qE "^src/"; then
    echo "Skipping (no code changes)"
    exit 0
fi
```

---

### **Problema 3: Error Recovery**

**Issue**: Si validate-references.sh falla, usuario queda bloqueado

**Soluciones**:
1. ✅ Error message claro + instructions para fix
2. ✅ `--no-verify` bypass si es urgente
3. ✅ Documentar en HOOKS_GUIDE.md

**Implementación**:
```bash
bash skills/documentation/resources/validate-references.sh || {
    echo ""
    echo "❌ VALIDATION FAILED"
    echo ""
    echo "Fix options:"
    echo "1. Edit CLAUDE.md/agents.md to resolve conflicts"
    echo "2. Run: bash skills/documentation/resources/validate-references.sh"
    echo "3. git add & retry commit"
    echo ""
    echo "OR bypass (if urgent):"
    echo "   git commit --no-verify"
    echo ""
    exit 1
}
```

---

## 📈 Plan Ejecutivo Paso a Paso

### **PASO 1: Crear archivos Phase 1** (2-3 horas)

- [ ] **1.1** Crear `llms.txt` (120 lines)
- [ ] **1.2** Crear `validate-references.sh` + `validate_references.py` (wrapper bash + parser python)
- [ ] **1.3** Crear `contexts/dev.md` (80 lines)
- [ ] **1.4** Crear `contexts/review.md` (80 lines)
- [ ] **1.5** Crear `contexts/research.md` (70 lines)
- [ ] **1.6** Crear `guides/QUICKSTART.md` (100 lines)
- [ ] **1.7** Crear `guides/ADVANCED.md` (150 lines)

**Validation**: 
```bash
find skills/documentation -type f | wc -l
# Debe haber 15 archivos (8 existentes + 7 nuevos)
```

---

### **PASO 2: Crear archivos Phase 2** (3-4 horas)

- [ ] **2.1** Crear `scripts/hooks/install-hooks.sh` (50 lines, executable)
- [ ] **2.2** Crear `scripts/hooks/pre-commit` (80 lines, executable)
- [ ] **2.3** Crear `scripts/hooks/run-doc-skill.sh` (60 lines, executable)
- [ ] **2.4** Crear `scripts/hooks/post-commit` (20 lines, executable) [OPCIONAL]
- [ ] **2.5** Crear `skills/documentation/resources/HOOKS_GUIDE.md` (120 lines)

**Validation**:
```bash
bash scripts/hooks/install-hooks.sh
git config --get core.hooksPath
# Debe imprimir: scripts/hooks
```

---

### **PASO 3: Actualizar SKILL.md** (1 hora)

- [ ] **3.1** Agregar secciones a `SKILL.md` (30 lines más)
- [ ] **3.2** Actualizar `resources/README.md` (50 lines más)
- [ ] **3.3** Actualizar `resources/examples/` si es necesario

**Validation**:
```bash
grep -c "Progressive Disclosure\|Git Hook\|contexts/" skills/documentation/SKILL.md
# Debe encontrar referencias a nuevas features
```

---

### **PASO 4: Testing & Documentation** (1-2 horas)

- [ ] **4.1** Crear PR de ejemplo con hook automation
- [ ] **4.2** Verificar que docs se actualicen automáticamente
- [ ] **4.3** Verificar que validate-references.sh detecte errors
- [ ] **4.4** Crear documento de integración (IMPLEMENTATION_COMPLETE.md)

---

## 📅 Timeline Estimado

| Fase | Tareas | Horas | Hito |
|------|--------|-------|------|
| **1** | llms.txt + validate-references.sh + contexts + guides | 2-3h | Core resources ready |
| **2** | install-hooks.sh + pre-commit + run-doc-skill + docs | 3-4h | Hooks installed & tested |
| **3** | Update SKILL.md + resources/README | 1h | Documentation complete |
| **4** | Testing + integration docs | 1-2h | 🎉 READY |
| **TOTAL** | ✅ | **7-10h** | Complete skill with automation |

---

## 🎯 Success Criteria

Skill se considera "DONE" cuando:

- ✅ llms.txt existe y es parseable (testing: `grep -E "Quick Reference|Documentation"`)
- ✅ validate-references.sh corre sin errores (testing: `bash ... validates CLAUDE.md`)
- ✅ contexts/ folder existe con 3 archivos (dev, review, research)
- ✅ QUICKSTART.md es < 100 lines, se completa en 5 min
- ✅ ADVANCED.md es > 100 lines, cubre patrones complejos
- ✅ Git hooks instalan sin errores (`bash scripts/hooks/install-hooks.sh`)
- ✅ `git config --get core.hooksPath` devuelve `scripts/hooks`
- ✅ Pre-commit hook ejecuta sin bloquear (test: `git commit --allow-empty`)
- ✅ SKILL.md + resources/README actualizados con referencias
- ✅ HOOKS_GUIDE.md documenta flujo completo

---

## 📚 Artifacts Generados

**Nuevos/Actualizados**:

```
llms.txt (NUEVO, root)

skills/documentation/
├── SKILL.md (updated)
├── IMPLEMENTATION_PLAN.md (este archivo)
├── resources/
│   ├── README.md (updated)
│   ├── validate-references.sh (NUEVO)
│   ├── validate_references.py (NUEVO)
│   ├── contexts/ (NUEVA CARPETA)
│   │   ├── dev.md
│   │   ├── review.md
│   │   └── research.md
│   ├── guides/ (NUEVA CARPETA)
│   │   ├── QUICKSTART.md
│   │   └── ADVANCED.md
│   ├── HOOKS_GUIDE.md (NUEVO)
│   └── [existing: templates, examples, checklist, workflows]

scripts/
└── hooks/ (NUEVA CARPETA)
    ├── install-hooks.sh
    ├── pre-commit
    ├── run-doc-skill.sh
    ├── post-commit
    └── README.md
```

---

## 🚀 Next Steps

1. **Review this plan** - ¿Ok con todas las fases y decisiones?
2. **Ejecutar FASE 1** - Crear core resources
3. **Testing básico** - Validar que archivos son útiles
4. **Ejecutar FASE 2** - Agregar git hooks
5. **Testing de hooks** - Validar que automatización funciona
6. **Ejecutar FASE 3** - Actualizar documentación
7. **Integración completa** - Merge a main, instalar en base-repo

---

## ✅ Decisiones Cerradas (post-review)

1. **llms.txt** vive en root (`./llms.txt`).
2. Hooks usan `git config core.hooksPath scripts/hooks` (sin symlinks).
3. **FAIL**: paths absolutos, paths inexistentes, CRITICAL fuera de orden, desync CLAUDE.md ↔ agents.md.
4. **WARN**: timestamps > 90 dias, links externos no resueltos, ctx sync falla.
5. Auto-stage solo docs (no `_ctx/` por default).
6. `validate-references.sh` usa parser Python (stdlib) para robustez.

---

**STATUS**: ✅ Plan listo para ejecutar. Esperando aprobación para empezar Fase 1.
