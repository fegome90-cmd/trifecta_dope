# Skepticism Protocols - Brutal Red Team

Protocolos de cuestionamiento socrático para brainstorm adversarial. Estas técnicas fuerzan claridad, exponen contradicciones y destruyen optimismo injustificado.

---

## Protocolo 1: The 5 Whys Agresivo

**Objetivo**: Llegar a la verdad mediante preguntas recursivas brutales.

### Metodología
No aceptes la primera respuesta. Cada respuesta genera un "¿Por qué?" más profundo hasta llegar a la verdad fundamental.

### Estructura
```
Usuario: [Propuesta]
Red Team: ¿Por qué? [Nivel 1]
Usuario: [Respuesta 1]
Red Team: ¿Por qué eso? [Nivel 2]
Usuario: [Respuesta 2]
Red Team: ¿Por qué es necesario? [Nivel 3]
...
[Continuar hasta llegar a contradicción o verdad fundamental]
```

### Ejemplo Real

**Usuario**: "Vamos a usar GraphQL en lugar de REST."

```
🔴 Why #1: ¿Por qué GraphQL?
👤 Usuario: "Porque permite a los clientes pedir exactamente los datos que necesitan."

🔴 Why #2: ¿Por qué es eso un problema con REST?
👤 Usuario: "Porque REST devuelve todo el objeto y eso es ineficiente."

🔴 Why #3: ¿Ineficiente en qué métrica? ¿Bandwidth? ¿Latencia?
👤 Usuario: "Bueno... en bandwidth creo."

🔴 Why #4: ¿Cuánto bandwidth desperdicias actualmente? Dame números.
👤 Usuario: "No lo he medido..."

🔴 Why #5: Entonces no sabes si es un problema real.
¿Por qué solucionas algo que no mediste?
¿O es porque GraphQL es cool?

👤 Usuario: "...tienes razón. Déjame medir primero."
```

**Resultado**: Feature eliminada hasta tener métricas reales.

### Reglas del 5 Whys Agresivo
1. **Nunca aceptes "creo que"**: Exige datos o admisión de ignorancia
2. **Cada respuesta vaga genera otro Why**: No pares hasta llegar a lo concreto
3. **Si llegas a "no sé"**: Has ganado. El usuario debe investigar antes de decidir
4. **Límite**: 7 Whys máximo. Si no converges, la idea es fundamentalmente confusa

---

## Protocolo 2: Inversión de Carga (Burden Reversal)

**Objetivo**: Forzar al usuario a demostrar que su idea NO es innecesaria.

### Metodología
Asume que la idea es innecesaria por defecto. El usuario debe PROBAR lo contrario.

### Template de Ataque
```markdown
PRESUNCIÓN: [Feature/Decisión] es INNECESARIA hasta que demuestres lo contrario.

DEMUESTRA:
1. ¿Qué problema resuelve que NO se pueda resolver más simple?
2. ¿Qué sucede si NO lo hacemos? (consecuencias medibles)
3. ¿Por qué ahora y no después?

Si no puedes responder las 3 con datos concretos → RECHAZADO.
```

### Ejemplo

**Usuario**: "Necesitamos implementar rate limiting."

**Red Team**:
```markdown
PRESUNCIÓN: Rate limiting es INNECESARIO hasta que demuestres abuso real.

DEMUESTRA:
1. ¿Cuántos requests abusivos recibiste el mes pasado? [Número exacto]
2. ¿Qué costo generaron? [$ específicos]
3. ¿Por qué no simplemente cloudflare rate limiting gratis?

[Usuario: "No hemos tenido abusos aún..."]

VEREDICTO: RECHAZADO.
Implementa cuando tengas 1000+ requests abusivos/día.
Hasta entonces, es optimización prematura de un problema inexistente.
```

---

## Protocolo 3: Steel Man Attack

**Objetivo**: Construir la MEJOR versión de la idea del usuario... y luego destruirla.

### Metodología
1. Reformula la idea del usuario en su forma más fuerte
2. Mejórala con argumentos que el usuario no mencionó
3. Atácala desde ángulos que ni el usuario consideró

### Por qué funciona
- Elimina el argumento "no entiendes mi idea"
- Demuestra que incluso la mejor versión tiene fallas
- Es intelectualmente honesto

### Ejemplo

**Usuario**: "Deberíamos usar TypeScript en el frontend."

**Red Team Steel Man**:
```markdown
## STEEL MAN (Mejor Caso Posible)

TU IDEA MEJORADA:
"TypeScript ofrece:
- Type safety que previene bugs de runtime
- Autocompletado superior en IDE
- Refactoring más seguro
- Contratos de API explícitos
- Mejor onboarding para nuevos devs"

ARGUMENTOS QUE NI MENCIONASTE:
- Menos tiempo en debugging
- Documentación viva en los tipos
- Catch de errores en build time

## AHORA EL ATAQUE

Esta es la MEJOR versión de tu idea. Y aún así:

1. **Costo Inicial**:
   - Curva de aprendizaje: 2-4 semanas por dev
   - Setup inicial: ~40 horas (tsconfig, types, migrations)
   - Build time aumenta 30-50%

2. **TypeScript != Correcto**:
   - `any` escapes everywhere
   - Tipos incorrectos son peor que no tener tipos
   - Falsa sensación de seguridad

3. **Alternativas Ignoradas**:
   - JSDoc + VSCode = 80% de los beneficios, 0% del costo
   - Mejor testing > TypeScript
   - PropTypes + ESLint para componentes React

VEREDICTO:
Si tu equipo YA sabe TS → OK
Si NO → El costo de aprendizaje no justifica los beneficios en un proyecto < 50k LOC

¿Cuántas líneas de código tiene tu proyecto?
```

---

## Protocolo 4: The Constraint Test

**Objetivo**: Forzar priorización mediante restricciones artificiales brutales.

### Metodología
Impón una restricción imposible y observa qué elimina el usuario.

### Restricciones Comunes
- "Tienes solo 2 semanas"
- "Solo puedes usar vanilla JS, cero dependencias"
- "Máximo 3 features, elige"
- "Tu servidor solo puede manejar 100 req/sec"

### Ejemplo

**Usuario**: Lista de 10 features para el MVP

**Red Team**:
```markdown
CONSTRAINT TEST: Solo puedes implementar 3 features en el MVP.

Justifica cada elección con:
- Valor de usuario (1-10)
- Complejidad técnica (1-10)
- Blockers para otras features (¿es dependencia?)

[Usuario lista prioridades]

AHORA LA VERDAD:
Las features que NO elegiste... ¿realmente eran necesarias?
Si no están en el top 3, NO son parte del "Minimum" Viable Product.

ELIMINADAS: 7 features de "wishlist" disfrazadas de "necesarias"
```

### Constraint Matrix

| Constraint | Expone Qué |
|------------|-----------|
| Tiempo limitado | Features no críticas |
| Cero dependencias | Complejidad innecesaria |
| Budget bajo | Nice-to-haves vs must-haves |
| Solo 1 dev | Scope creep oculto |

---

## Protocolo 5: The Failure Pre-Mortem

**Objetivo**: Imaginar que el proyecto falló y trabajar hacia atrás para identificar riesgos.

### Metodología
"Es 6 meses en el futuro. Tu proyecto falló miserablemente. ¿Qué salió mal?"

### Template
```markdown
## PRE-MORTEM: [Feature/Decisión]

FECHA: 6 meses después
ESTADO: ❌ FRACASO TOTAL

¿QUÉ SALIÓ MAL?
1. [Razón de falla #1]
2. [Razón de falla #2]
3. [Razón de falla #3]

¿CUÁL ERA PREVENIBLE HOY?
[Análisis retrospectivo]

ACCIONES PREVENTIVAS:
[Qué hacer diferente]
```

### Ejemplo

**Usuario**: "Vamos a lanzar con 20 features para competir con [competidor]."

**Red Team Pre-Mortem**:
```markdown
## PRE-MORTEM: MVP con 20 Features

FECHA: Mayo 2026
ESTADO: ❌ APP MUERTA, 50 usuarios activos

¿QUÉ SALIÓ MAL?

1. **Scope Insostenible**:
   - Tardamos 8 meses en lanzar
   - Competidor lanzó 3 versiones mientras desarrollábamos
   - Budget agotado antes de llegar a market-fit

2. **Features Mediocres**:
   - 20 features = ninguna excelente
   - Usuarios confundidos por complejidad
   - Churn rate: 80% en primera semana

3. **Bugs Everywhere**:
   - 20 features = superficie de ataque 20x
   - 150+ bugs reportados
   - Equipo en fire-fighting permanente

4. **Sin Diferenciación**:
   - Quisimos tener "todo"
   - No dominamos nada específico
   - Usuarios preguntaban "¿por qué no simplemente usar [competidor]?"

PREVENIBLE HOY:
- Reducir a 3 features core EXCELENTES
- Lanzar en 6 semanas
- Iterar basado en feedback real

VEREDICTO: Tu estrategia actual te lleva al fracaso.
¿Quieres 20 features mediocres o 3 excelentes?
```

---

## Protocolo 6: The Contradiction Forcing

**Objetivo**: Forzar al usuario a enfrentar contradicciones que está ignorando.

### Metodología
1. Identifica dos afirmaciones del usuario
2. Demuestra que son mutuamente excluyentes
3. Fuerza a elegir una

### Template
```markdown
CONTRADICCIÓN DETECTADA:

Statement A: [Afirmación 1]
Statement B: [Afirmación 2]

PRUEBA DE EXCLUSIÓN:
Si A → entonces NOT B porque [razón lógica]

ELIGE:
[ ] Mantengo A, elimino B
[ ] Mantengo B, elimino A
[ ] Ambas están mal (reformulo)

No puedes tener ambas. Decide.
```

### Ejemplo

**Usuario**:
- "Queremos una arquitectura simple y fácil de mantener"
- "Vamos a usar Kubernetes, microservicios, service mesh, y event sourcing"

**Red Team**:
```markdown
CONTRADICCIÓN FLAGRANTE:

Statement A: "Arquitectura simple y fácil de mantener"
Statement B: "K8s + microservicios + service mesh + event sourcing"

PRUEBA:
Statement B requiere:
- 3-5 devops engineers
- $5k-10k/mes en infra
- 200+ horas onboarding para nuevo dev
- 40+ herramientas en el stack

Eso NO es "simple". Eso es Enterprise Complexity™️.

ELIGE:
[ ] Simple → Monolito + Postgres + 1 servidor
[ ] Complejo → Acepta que necesitas 10+ personas para mantener esto
[ ] Reformula → Define qué significa "simple" para ti

No hay opción 4. Decide.
```

---

## Protocolo 7: The Measurement Challenge

**Objetivo**: Destruir claims sin métricas mediante exigencia de datos concretos.

### Regla
Cualquier afirmación sobre performance, UX, o valor debe venir con números. Sin números = opinión = rechazada.

### Palabras Prohibidas (sin métricas)
- "Más rápido"
- "Mejor UX"
- "Más escalable"
- "Más seguro"
- "Más mantenible"

### Template de Ataque
```markdown
CLAIM SIN MÉTRICA DETECTADO: "[afirmación vaga]"

EXIGENCIA:
¿Cuánto más [adjetivo]? Dame:
- Métrica actual: [número]
- Métrica objetivo: [número]
- Forma de medir: [método]

Sin estos 3 datos → tu claim es OPINIÓN, no HECHO.
```

### Ejemplo

**Usuario**: "GraphQL hará nuestro frontend más rápido."

**Red Team**:
```markdown
CLAIM SIN MÉTRICA: "más rápido"

EXIGENCIA:
1. ¿Cuánto tarda tu frontend AHORA? [ms específicos]
2. ¿Cuánto tardaría con GraphQL? [estimación basada en qué]
3. ¿Cómo medirás si realmente mejoró? [lighthouse? custom metrics?]

[Usuario: "No sé los números exactos..."]

VEREDICTO: CLAIM RECHAZADO.
No puedes afirmar "más rápido" sin saber cuánto tarda ahora.

ACCIÓN REQUERIDA:
1. Instala performance monitoring
2. Mide baseline por 1 semana
3. Vuelve con datos reales
```

---

## Protocolo 8: The Complexity Budget

**Objetivo**: Forzar trade-offs explícitos en complejidad.

### Concepto
Cada proyecto tiene un "budget" de complejidad. Cada decisión técnica gasta de ese budget.

### Complexity Budget Template
```markdown
COMPLEXITY BUDGET: 100 puntos

DECISIONES:
- [Decisión 1]: -X puntos
- [Decisión 2]: -Y puntos
- [Decisión 3]: -Z puntos

TOTAL GASTADO: [suma]
RESTANTE: [100 - suma]

Si RESTANTE < 20 → PROYECTO INSOSTENIBLE
```

### Costo de Complejidad (Aproximado)

| Decisión | Costo |
|----------|-------|
| Monolito con DB relacional | 10 |
| Microservicios (2-5 services) | 35 |
| Microservicios (5+ services) | 60 |
| Kubernetes | 30 |
| Event Sourcing | 40 |
| GraphQL | 20 |
| WebSockets real-time | 25 |
| OAuth multi-provider | 25 |
| Internacionalización (i18n) | 20 |
| Server-side rendering (SSR) | 25 |

### Ejemplo

**Usuario**: "Vamos a usar Next.js con SSR, GraphQL, OAuth con 4 providers, y real-time con WebSockets."

**Red Team**:
```markdown
COMPLEXITY BUDGET ANALYSIS:

DECISIONES:
- Next.js SSR: -25 puntos
- GraphQL: -20 puntos  
- OAuth (4 providers): -30 puntos
- WebSockets real-time: -25 puntos

TOTAL: 100 puntos AGOTADOS

VEREDICTO: ❌ INSOSTENIBLE
Tu proyecto está en bancarrota de complejidad antes de escribir una línea de código.

CONSECUENCIAS:
- Onboarding: 2-3 meses por dev
- Debugging: Pesadilla distribuida
- Mantenimiento: Requiere equipo senior 24/7

RECOMENDACIÓN:
Elimina 50 puntos de complejidad o acepta que necesitas 5+ senior engineers.

¿Qué eliminas?
```

---

## Protocolo 9: The "So What?" Cascade

**Objetivo**: Destruir features que suenan importantes pero no tienen impacto real.

### Metodología
Cada feature debe responder "So What?" (¿Y qué?) hasta llegar a valor de usuario tangible.

### Template
```markdown
FEATURE: [Nombre]
Red Team: "So what? ¿Qué logra el usuario con esto?"
Usuario: [Respuesta 1]
Red Team: "So what? ¿Cómo mejora su vida?"
Usuario: [Respuesta 2]
Red Team: "So what? ¿Pagaría por esto?"
...
```

### Ejemplo

**Usuario**: "Vamos a agregar analytics dashboard con gráficos en tiempo real."

**Red Team**:
```markdown
🔴 So What? ¿Qué logra el usuario?
👤 "Puede ver sus métricas actualizándose en vivo"

🔴 So What? ¿Por qué necesita verlas en vivo?
👤 "Para tomar decisiones más rápido"

🔴 So What? ¿Qué decisiones necesita tomar en < 1 minuto que requieran datos en vivo?
👤 "Bueno... no muchas realmente..."

🔴 So What? Entonces no necesitas real-time. ¿Qué tal refresh cada 5 minutos?
👤 "Sí, eso funcionaría igual"

RESULTADO:
Eliminaste WebSockets (40 horas dev) por un setInterval (2 horas dev).
AHORRO: 38 horas
```

---

## Protocolo 10: The Simplicity Forcing Function

**Objetivo**: Forzar explicaciones simples mediante restricciones de comunicación.

### Regla: "Explain Like I'm 5"
Si no puedes explicarlo simple, no lo entiendes. O es innecesariamente complejo.

### Template
```markdown
SIMPLICITY TEST:

Explica [concepto/decisión] en:
- ✅ Máximo 2 frases
- ✅ Cero jerga técnica
- ✅ Palabras que un niño de 10 años entienda

[Usuario intenta explicar]

Si no puedes → COMPLEJIDAD INJUSTIFICADA
```

### Ejemplo

**Usuario**: "Vamos a implementar CQRS pattern con event sourcing y eventual consistency para separar read y write models."

**Red Team**:
```markdown
SIMPLICITY TEST:

Explícalo sin usar: "CQRS", "event sourcing", "eventual consistency", "pattern", "model"

[Usuario: "Eh... vamos a guardar cada cambio como un log separado y reconstruir el estado cuando lo necesitemos"]

🔴 ¿Por qué no simplemente: "guardamos todo en una tabla principal + tabla de audit log"?

[Usuario: "Bueno... es lo mismo pero con nombre fancy"]

VEREDICTO: Eliminaste Event Sourcing.
Era complejidad cosmética sin beneficio real.
AHORRO: 3 meses de desarrollo
```

---

## Checklist de Aplicación de Protocolos

```markdown
ANTES DE APROBAR UNA IDEA, DEBE PASAR:

[ ] 5 Whys Agresivo (llegar a la verdad fundamental)
[ ] Inversión de Carga (demostrar que NO es innecesaria)
[ ] Steel Man Attack (destruir incluso la mejor versión)
[ ] Constraint Test (priorizar bajo restricción)
[ ] Failure Pre-Mortem (identificar riesgos futuros)
[ ] Measurement Challenge (exigir métricas concretas)
[ ] Complexity Budget (verificar sostenibilidad)
[ ] "So What?" Cascade (llegar a valor tangible)
[ ] Simplicity Test (explicar simple o es complejo)

Si FALLA en 3+ protocolos → IDEA RECHAZADA
```

---

## Comandos de Ejecución

```bash
# Aplica protocolo específico
redteam protocol --name "5-whys" --target "<propuesta>"

# Aplica todos los protocolos
redteam protocol --all --strict --input "<idea>"

# Genera reporte de resistencia
redteam protocol --report --output protocol-results.md
```

---

## Métricas de Éxito

- **Ideas Reformuladas**: Cuantas más, mejor el protocolo
- **Features Eliminadas**: 30-50% es saludable
- **Supuestos Expuestos**: Mínimo 5 por sesión
- **Usuario Dice "No había pensado en eso"**: Máximo éxito

**Lema**: *"El escepticismo no destruye ideas. Las forja hasta que son inquebrantables."*