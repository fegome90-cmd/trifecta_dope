# Attack Vectors - Brutal Red Team

Catálogo de vectores de ataque lógico para desmantelar propuestas en brainstorm. Cada vector está diseñado para exponer debilidades estructurales, supuestos ocultos y sesgos cognitivos.

---

## Vector 1: Contradicción Interna (Internal Inconsistency)

**Objetivo**: Exponer cuando dos afirmaciones en la misma propuesta se contradicen entre sí.

### Técnica
1. Identifica dos statements del usuario
2. Muestra que si A es verdad, B no puede serlo
3. Fuerza al usuario a elegir y justificar

### Ejemplo
**Usuario**: "Necesitamos microservicios para escalar. Pero queremos deploy simple sin DevOps complejo."

**Attack**:
```
CONTRADICCIÓN DETECTADA:
- Statement A: "Microservicios para escalar"
- Statement B: "Deploy simple"

Si (A) entonces (NOT B). Los microservicios REQUIEREN:
- Service discovery
- API Gateway
- Distributed logging
- Circuit breakers
- Container orchestration

Eso NO es "simple". ¿Cuál es tu prioridad real: escala o simplicidad?
No puedes tener ambas sin costos de infraestructura.
```

### Plantilla de Ataque
```
CONTRADICCIÓN: [Statement A] ⊗ [Statement B]
PRUEBA: Si [A] → entonces [consecuencia que niega B]
CONCLUSIÓN: Debes elegir. Justifica cuál es prioritario.
```

---

## Vector 2: Costo de Oportunidad (Opportunity Cost)

**Objetivo**: Forzar al usuario a reconocer qué NO hará por hacer esto.

### Técnica
1. Estima tiempo/complejidad de la propuesta
2. Lista 3 alternativas que podrías hacer en ese tiempo
3. Pregunta: "¿Esto es más valioso que las 3 alternativas juntas?"

### Ejemplo
**Usuario**: "Vamos a implementar OAuth completo con Google, GitHub, Twitter."

**Attack**:
```
COSTO DE OPORTUNIDAD:
Implementar OAuth completo = ~40 horas ingeniero

ALTERNATIVAS EN 40 HORAS:
1. Email/password + password reset funcional
2. 10 features core del producto
3. Sistema completo de onboarding

PREGUNTA: ¿Cuántos usuarios realmente necesitan login social vs email?
Si < 20% de tu target, estás sacrificando 10 features por conveniencia de una minoría.

¿Estás construyendo para usuarios o para tu CV?
```

### Plantilla de Ataque
```
COSTO ESTIMADO: [X horas/días]
ALTERNATIVAS:
1. [Feature A]
2. [Feature B]
3. [Feature C]
PREGUNTA: ¿Esto es 3x más valioso que las alternativas?
```

---

## Vector 3: Complejidad Innecesaria (Accidental Complexity)

**Objetivo**: Identificar cuando la solución es más compleja que el problema.

### Técnica (Occam's Razor Enforcement)
1. Reduce el problema a su esencia
2. Propón la solución más simple posible
3. Pregunta: "¿Por qué tu propuesta es mejor que esto?"

### Ejemplo
**Usuario**: "Vamos a usar Redux Toolkit + RTK Query + Redux Saga para manejo de estado."

**Attack**:
```
COMPLEJIDAD DETECTADA:
Tu stack: Redux Toolkit + RTK Query + Saga = 3 librerías, ~500KB, curva aprendizaje alta

SOLUCIÓN SIMPLE:
- React.useState para UI state
- fetch + SWR para server state
- Total: 1 librería, ~50KB, API nativa

PREGUNTA: ¿Tu app tiene > 50 componentes con estado compartido complejo?
Si NO → tu propuesta es overkill por 10x

Defendela con métricas reales de complejidad, no con "es el estándar de la industria".
```

### Test de Necesidad
```javascript
const needsComplexity = (
  components > 50 &&
  sharedState > 20 &&
  asyncOperations > 30 &&
  stateInterdependencies > 15
);

if (!needsComplexity) {
  return "OVERKILL DETECTADO";
}
```

---

## Vector 4: Sesgos Cognitivos (Cognitive Bias Detection)

**Objetivo**: Exponer cuando las decisiones vienen de sesgos, no de lógica.

### 4.1 Confirmation Bias (Sesgo de Confirmación)
**Síntoma**: Usuario solo menciona pros, ignora cons.

**Attack**:
```
SESGO DETECTADO: Solo veo ventajas. Dame 3 desventajas reales.
Si no puedes, no entiendes tu propia propuesta.
```

### 4.2 Sunk Cost Fallacy
**Síntoma**: "Ya invertimos X horas en [librería/stack], no podemos cambiar."

**Attack**:
```
FALACIA: El tiempo ya gastado es IRRELEVANTE para decisiones futuras.
PREGUNTA: Si empezaras hoy de cero, ¿elegirías esta solución?
Si NO → abandónala. El costo hundido no se recupera continuando.
```

### 4.3 Bandwagon Effect (Moda Tecnológica)
**Síntoma**: "Todo el mundo usa [framework], debe ser bueno."

**Attack**:
```
FALACIA AD POPULUM: Popularidad ≠ Idoneidad
EJEMPLOS HISTÓRICOS:
- jQuery fue "el estándar" → ahora es legacy
- MongoDB fue "webscale" → muchos migraron a Postgres

PREGUNTA: ¿Elegiste esto por análisis objetivo o por FOMO?
```

### 4.4 Not Invented Here (NIH Syndrome)
**Síntoma**: "Vamos a construir nuestro propio [auth/ORM/queue] porque los existentes no son perfectos."

**Attack**:
```
SÍNDROME NIH DETECTADO:
Tu plan: Construir [sistema complejo] desde cero

REALIDAD:
- Llevas 6 meses
- Introduce 10+ bugs críticos
- Nadie más que tú lo entiende
- Abandonas el proyecto

ALTERNATIVA: Usa [librería establecida] + contribuye fixes upstream
RESULTADO: Feature lista en 2 días, mantenida por comunidad

¿Tu ego vale 6 meses de desarrollo?
```

---

## Vector 5: Valor Fantasma (Phantom Value)

**Objetivo**: Destruir features que solo existen en tu imaginación optimista.

### Técnica: "The Usage Test"
Pregunta radical: *"Si implementas esto y NADIE lo usa, ¿cómo te sentirías?"*

### Ejemplo
**Usuario**: "Vamos a agregar modo oscuro (dark mode)."

**Attack**:
```
VALOR FANTASMA ALERT:
¿Cuántos usuarios te PIDIERON dark mode? [Espera respuesta]

Si 0 → Estás inventando demanda
Si < 10% → No es prioritario
Si > 50% → Ok, pero DESPUÉS de features core

DATO: Implementar dark mode = 20-40 horas
- CSS variables
- Toggle UI
- Persistencia de preferencia
- Testing en ambos modos

ALTERNATIVA: Usa prefers-color-scheme nativo del OS
RESULTADO: 0 horas dev, soporte automático

¿Estás construyendo para usuarios o para Hacker News karma?
```

### Red Flags de Valor Fantasma
- "Los usuarios lo amarían si existiera"
- "Es una best practice de UX"
- "Todos nuestros competidores lo tienen"
- "Se ve más profesional"

**Response Template**:
```
RED FLAG: [Frase del usuario]
TRADUCCIÓN: "No tengo evidencia de demanda real"
PREGUNTA: ¿Cuántos usuarios perdiste por NO tener esto?
SI 0 → NO ES PRIORIDAD
```

---

## Vector 6: Premature Optimization

**Objetivo**: Destruir optimizaciones sin métricas actuales.

### Técnica
1. Pregunta: "¿Cuál es el problema de performance ACTUAL?"
2. Si no hay métricas → la optimización es prematura
3. Fuerza a establecer baseline antes de optimizar

### Ejemplo
**Usuario**: "Vamos a usar Redis para caché porque la DB será lenta."

**Attack**:
```
OPTIMIZACIÓN PREMATURA DETECTADA:

PREGUNTAS:
1. ¿Cuál es tu query time actual? [No sé] → NO OPTIMICES AÚN
2. ¿Cuántos requests por segundo esperas? [No medí] → NO AGREGUES REDIS
3. ¿Probaste índices en Postgres? [No] → ESA ES TU PRIMERA OPTIMIZACIÓN

REGLA DE ORO:
1. Medir problema actual
2. Optimizar query/schema
3. Agregar índices
4. Considerar cache SOLO si pasos 1-3 fallan

Redis sin métricas = Complejidad operacional por problema imaginario.
```

### Donald Knuth Quote
> "Premature optimization is the root of all evil"

**Red Team Translation**:
> "Si no tienes un profiler corriendo, tu 'optimización' es masturbación intelectual."

---

## Vector 7: Hidden Assumptions (Supuestos Ocultos)

**Objetivo**: Exponer supuestos que el usuario ni siquiera sabe que está haciendo.

### Técnica: "The Assumption Drill"
Identifica verbos en subjuntivo y conviértelos en afirmaciones explícitas.

### Ejemplo
**Usuario**: "Los usuarios podrían querer exportar sus datos."

**Attack**:
```
SUPUESTO OCULTO:
"podrían querer" = "No sé si quieren"

EXPLÍCITALO:
SUPUESTO: Usuarios quieren exportar datos
EVIDENCIA: [Ninguna]
COSTO: 15 horas dev

PREGUNTA CORRECTA:
¿Cuántos usuarios te PIDIERON export?
¿Es requisito legal (GDPR)?

Si NO a ambas → ELIMINA LA FEATURE hasta tener demanda real.
```

### Lista de Frases de Supuesto Oculto
- "Los usuarios podrían..."
- "Probablemente necesiten..."
- "Es mejor tener por si acaso..."
- "En el futuro vamos a necesitar..."

**Red Team Rule**: Toda frase con "podría/probablemente/futuro" es supuesto sin validar.

---

## Vector 8: Scope Creep Predictivo

**Objetivo**: Predecir cómo la idea evolucionará en complejidad descontrolada.

### Técnica: "The 6-Month Projection"
Proyecta cómo la feature simple de hoy se convierte en pesadilla en 6 meses.

### Ejemplo
**Usuario**: "Solo vamos a agregar un campo 'tags' a los posts."

**Attack**:
```
PROYECCIÓN DE SCOPE CREEP:

MES 1: Campo 'tags' simple (array de strings)
MES 2: "Necesitamos autocompletar tags existentes"
MES 3: "Los tags deben tener jerarquía (categories > subcategories)"
MES 4: "Necesitamos búsqueda por tags"
MES 5: "Los tags deben ser editables globalmente"
MES 6: "Necesitamos analytics de tags más usados"

RESULTADO: Lo que empezó como "un campo" ahora es un sistema completo de taxonomía.

PREGUNTA: ¿Estás dispuesto a mantener esa complejidad?
Si NO → Redefine el scope con límites DUROS desde día 1.
```

### Scope Creep Protection
```markdown
## Feature: Tags
SCOPE MÁXIMO:
- Array de strings
- Sin autocompletar
- Sin jerarquía
- Sin edición global

TODO LO DEMÁS RECHAZADO POR DEFECTO.
```

---

## Vector 9: Technical Debt Forecast

**Objetivo**: Forzar reconocimiento explícito de deuda técnica que introduces.

### Técnica
Cada decisión técnica genera deuda futura. Hazla visible.

### Ejemplo
**Usuario**: "Vamos a usar MongoDB porque es más flexible."

**Attack**:
```
DEUDA TÉCNICA INTRODUCIDA:

DECISIÓN: MongoDB (schema-less)
DEUDA GENERADA:
1. Inconsistencias de datos (sin schema enforcement)
2. Queries complejas (no hay JOINs nativos)
3. Migraciones manuales (sin ALTER TABLE)
4. Testing difícil (datos inconsistentes)

COSTO DE PAGO FUTURO:
- 2-3 meses de refactoring cuando necesites relaciones
- 50+ bugs de producción por datos mal formados

ALTERNATIVA: Postgres con JSONB
BENEFICIO: Schema + flexibilidad
DEUDA: Cero

¿Tu "flexibilidad" vale 3 meses de dolor futuro?
```

---

## Vector 10: The Simplicity Challenge

**Objetivo**: Forzar al usuario a explicar su idea en < 3 frases sin jerga técnica.

### Técnica: "Explain to a 10-Year-Old"
Si no puedes explicarlo simple, no lo entiendes.

### Ejemplo
**Usuario**: "Vamos a implementar un event-driven architecture con CQRS y Event Sourcing para separar reads y writes."

**Attack**:
```
SIMPLICITY CHALLENGE:
Explícame esto como si tuviera 10 años. Sin palabras: "event-driven", "CQRS", "sourcing".

[Usuario balbucea]

TRADUCCIÓN REAL:
"Quiero guardar cada cambio en el sistema como un log separado."

PREGUNTA: ¿Por qué no simplemente guardar el estado actual + audit log?
99% de apps NO necesitan Event Sourcing.

¿Tu sistema realmente necesita reconstruir estado histórico?
Si NO → Eliminaste 3 meses de complejidad.
```

---

## Matriz de Priorización de Ataques

Usa esta matriz para decidir qué vector aplicar:

| Síntoma en Propuesta | Vector Recomendado | Severidad |
|----------------------|-------------------|-----------|
| Dos afirmaciones incompatibles | Vector 1: Contradicción | 🔴 Alta |
| "Necesitamos X porque es moderno" | Vector 4: Bandwagon | 🔴 Alta |
| Feature sin usuarios que la pidan | Vector 5: Valor Fantasma | 🔴 Alta |
| "Vamos a optimizar antes de lanzar" | Vector 6: Premature Opt | 🟡 Media |
| "Los usuarios podrían..." | Vector 7: Hidden Assumptions | 🟡 Media |
| Stack con > 5 dependencias nuevas | Vector 3: Complejidad | 🔴 Alta |
| "Solo un campo más" | Vector 8: Scope Creep | 🟡 Media |
| No puede explicarlo simple | Vector 10: Simplicity | 🔴 Alta |

---

## Comandos de Ejecución

```bash
# Aplica vector específico
redteam attack --vector contradiction --target "<statement>"

# Auto-detecta mejor vector
redteam attack --auto --input "<propuesta>"

# Combina múltiples vectores
redteam attack --vectors "contradiction,opportunity-cost" --target "<idea>"
```

---

## Métricas de Éxito del Attack

- **Supuestos Expuestos**: Cuantos más, mejor el ataque
- **Contradicciones Encontradas**: Mínimo 1 por propuesta compleja
- **Features Eliminadas**: Si eliminaste 3+ features, el ataque fue efectivo
- **Usuario Reformula Idea**: Éxito total si el usuario redefine completamente su propuesta

**Lema**: *"Un ataque exitoso no destruye ideas; las refina hasta que son indestructibles."*