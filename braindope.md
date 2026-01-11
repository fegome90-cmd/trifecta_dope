# Braindope: CLI Smart Search UX

**Estado**: ✅ Convergido
**Fecha Inicio**: 2026-01-04
**Fecha Última Actualización**: 2026-01-04
**Participantes**: Usuario (Executive) | Red Team (Antigravity)

---

## 1. Contexto de Proyecto

### Estado Actual

- `trifecta ctx search` realiza búsqueda exacta (grep/glob).
- Usuarios (y LLMs) confunden esto con RAG semántico.
- Resultados vacíos generan frustración o alucinaciones en agentes.

### Nueva Fase Propuesta

- Mejorar la UX de `ctx search` para manejar consultas de lenguaje natural.

### Objetivos de la Fase

- Reducir fricción cuando el usuario busca "cómo hacer X".
- Diferenciar explícitamente entre Contexto (determinista) y RAG (probabilista).
- Mantener la herramienta "snappy" (baja latencia).

### Restricciones Conocidas

- **Latencia**: CLI debe responder en <500ms.
- **Arquitectura**: No acoplar código Python con Makefile o herramientas externas frágiles.
- **Dependencias**: No agregar NLP pesado (spacy/nltk) al core.

---

## 2. Propuesta Inicial (Versión 0)

### Idea Original

"Agregar un banner [NOTE] al inicio de `ctx search` explicando que no es RAG y que se deben usar keywords exactas."

### Stack/Decisiones Técnicas Propuestas

- `typer.echo` con color amarillo.
- Texto estático en `cli.py`.

### Supuestos Implícitos

- El usuario (o LLM) leerá el banner antes de ver los resultados.
- El usuario entenderá la diferencia y reformulará su query por sí mismo.

---

## 3. Debate (Rondas de Ataque)

### 📍 Ronda 1: Banner Blindness

**Timestamp**: 18:05

**Red Team ataca**:
"Los LLMs (y usuarios) tienen 'ceguera de banner'. Ignoran el boilerplate y miran el output. Si el output es 0 resultados, alucinarán una razón en lugar de leer tu nota. ¿Es esto 'Security Theater'?"

**Usuario responde**:
"Es mejor que nada. Al menos está documentado."

**Red Team contraataca**:
"La documentación pasiva en tiempo de ejecución es ruido. Si sabes que el usuario falló por usar lenguaje natural, ¿por qué no detectarlo y fallar con un error estructurado?"

**Resultado de Ronda**:

- [x] Idea destruida: Banner Pasivo
- [x] Nueva Propuesta: Intent Detection (Regex para 'how', 'what', 'is')
- [ ] Se identificó nuevo supuesto: Podemos detectar intención con regex simple.

**Aprendizajes**:

- El texto pasivo es una defensa débil.
- Necesitamos feedback activo.

---

### 📍 Ronda 2: Intent Detection Fragility

**Timestamp**: 18:10

**Red Team ataca**:
"Tu propuesta de 'Intent Detection' (regex) es frágil.

1. Falsos positivos: Buscar el string literal 'how to X'.
2. Mantenimiento: Lista de stopwords en inglés hardcodeada en Python. ¿Y si escribo en español?
3. User Hostile: Bloquear al usuario y regañarlo es peor UX que dar 0 resultados."

**Usuario responde**:
"Entonces, ¿qué hacemos? ¿Ejecutar el RAG automáticamente si falla?"

**Red Team contraataca**:
"Esa es una hipótesis mejor: 'Auto-Escalation'. Si 0 hits -> Run `minirag-query`. Cero fricción."

**Resultado de Ronda**:

- [x] Idea destruida: Intent Detection (Regex)
- [x] Nueva Propuesta: Auto-Escalation (Fallback automático a MiniRAG)

**Aprendizajes**:

- Heurísticas en código = Deuda técnica.
- Bloquear es malo. Resolver es mejor.

---

### 📍 Ronda 3: Auto-Escalation Latency & Coupling

**Timestamp**: 18:15

**Red Team ataca**:
"Auto-Escalation suena mágico, pero:

1. **Latencia**: MiniRAG tarda 5s en arrancar (Python + Ollama). El CLI parecerá congelado.
2. **Acoplamiento**: Llamar a `make minirag-query` desde Python acopla el binario a un Makefile externo. Si cambia el target, rompes el binario.
3. **Opacidad**: El usuario pidió contexto (determinista) y le das RAG (probabilista) sin avisar. Confusión peligrosa."

**Usuario responde**:
"Touché. No podemos permitir latencia de 5s ni acoplamiento frágil."

**Red Team contraataca**:
"Regresemos a la filosofía Unix. Haz una cosa bien. Si fallas, sugiere la alternativa pero no la ejecutes.
Propuesta: 'Helpful Failure'.
Si 0 hits -> Exit 0 -> Imprimir sugerencia en stderr: '? Did you mean `make minirag-query`?'"

**Resultado de Ronda**:

- [x] Idea destruida: Auto-Escalation
- [x] Idea Validada: Helpful Failure (Sugerencia en Stderr)

**Aprendizajes**:

- Automatizar procesos pesados en el CLI es mala UX.
- Enseñar es mejor que ocultar.

---

## 4. Supuestos Destruidos / Validados

### ❌ Supuestos Destruidos

| Supuesto | Por qué era falso | Impacto |
|----------|-------------------|---------|
| "El usuario lee banners" | Banner Blindness en LLMs | Eliminó Banner Pasivo |
| "Podemos detectar lenguaje natural con regex" | Frágil, no i18n, falsos positivos | Eliminó Intent Detection |
| "Vale la pena automatizar el fallback" | Latencia inaceptable (>5s), acoplamiento | Eliminó Auto-Escalation |

### ✅ Supuestos Validados

| Supuesto | Evidencia | Confianza |
|----------|-----------|-----------|
| "El usuario necesita saber que existe MiniRAG" | Confusión recurrente Context vs RAG | Alta |
| "Sugerir es mejor que imponer" | Unix Philosophy, zero latency | Alta |

---

## 5. Ideas Eliminadas (Graveyard)

### 💀 Feature: Passive Banner

**Razón de Eliminación**: Weak defense. Ignorado por LLMs.
**Ahorro Estimado**: Ruido visual.

### 💀 Feature: Heuristic Intent Detection

**Razón de Eliminación**: Deuda técnica (stopwords lists), Falsos positivos bloqueantes.
**Alternativa Adoptada**: Verificación post-search (0 hits).

### 💀 Feature: Auto-Escalation (Subprocess Call)

**Razón de Eliminación**: Latencia de 5s+ destruye la experiencia "snappy". Acoplamiento a Makefile.
**Alternativa Adoptada**: Suggestion Footer.

---

## 6. Propuesta Refinada (Versión Final)

### Stack Validado

- **Python Standard Lib** - *Justificación: Sin nuevas dependencias.*
- **Typer/Click Stderr** - *Justificación: Separar output real de sugerencias.*

### Arquitectura Final

Modificar `SearchUseCase` o `cli.py`:

- Ejecutar búsqueda normal.
- Si `results == 0`:
  - Imprimir sugerencia formateada (Cyan/Yellow) en `stderr`.
  - No afectar `stdout` (para que pipes funcionen).

### Features Core (Prioritizadas)

1. **Suggestion Footer** - Value Score: 90 - *Bajo costo, alto valor educativo.*

---

## 7. Contrato de Fase (Invariantes)

### Reglas Inquebrantables

1. **NO bloquear** una búsqueda válida (incluso si parece lenguaje natural).
2. **NO automatizar** procesos que tomen >500ms sin spinner/consentimiento.
3. **NO acoplar** código Python a targets de Makefile hardcodeados en lógica core.

### Exit Criteria

- [ ] `trifecta ctx search -q "blah"` (0 hits) muestra sugerencia.
- [ ] `trifecta ctx search -q "Trifecta"` (1+ hits) NO muestra sugerencia.
- [ ] Output de sugerencia va a stderr (no rompe `| jq`).

---

## 10. Firma del Debate

**Fecha de Convergencia**: 2026-01-04 18:25
**Estado Final**: ✅ CONVERGIDO
**Listo para Implementación**: Sí
