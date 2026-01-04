# Braindope Format - Brutal Red Team

Plantilla y guía para estructurar el documento `braindope.md` - el registro vivo del debate adversarial entre usuario y red team durante brainstorm de nuevas fases.

---

## Qué es un Braindope

**Definición**: Documento evolutivo que captura el proceso completo de refinamiento de una idea desde su propuesta inicial hasta su forma final validada.

**Por qué "Braindope"**:
- **Brain**: Ideas y razonamiento
- **Dope**: Contenido crudo y sin filtro (slang)
- **Output**: Documento de trabajo que evoluciona

**No es**:
- ❌ Documentación formal final
- ❌ Especificación técnica detallada
- ❌ Registro bonito para stakeholders

**Es**:
- ✅ Registro honesto del debate
- ✅ Historia de ideas destruidas y por qué
- ✅ Contexto para decisiones futuras
- ✅ Prueba de que pensaste críticamente

---

## Estructura Obligatoria

### Template Base

```markdown
# Braindope: [Nombre de Fase]
**Estado**: [🔴 En Cuestionamiento | 🟡 Refinando | ✅ Convergido | ❌ Abandonado]
**Fecha Inicio**: [YYYY-MM-DD]
**Fecha Última Actualización**: [YYYY-MM-DD]
**Participantes**: [Usuario | Red Team]

---

## 1. Contexto de Proyecto

### Estado Actual
[Qué ya existe en el proyecto]

### Nueva Fase Propuesta
[Qué se quiere construir ahora]

### Objetivos de la Fase
- [Objetivo 1]
- [Objetivo 2]
- [Objetivo 3]

### Restricciones Conocidas
- [Restricción técnica 1]
- [Restricción de tiempo/budget 2]
- [Restricción de recursos 3]

---

## 2. Propuesta Inicial (Versión 0)

### Idea Original
[La primera propuesta del usuario, sin filtro]

### Stack/Decisiones Técnicas Propuestas
- [Tecnología 1]
- [Tecnología 2]
- [Arquitectura propuesta]

### Supuestos Implícitos
[Red team identifica supuestos que el usuario no mencionó explícitamente]

---

## 3. Debate (Rondas de Ataque)

### 📍 Ronda 1: [Tema de Ataque]
**Timestamp**: [HH:MM]

**Red Team ataca**:
[Pregunta o desafío socrático]

**Usuario responde**:
[Defensa o reformulación]

**Red Team contraataca**:
[Siguiente nivel de cuestionamiento]

**Usuario responde**:
[Nueva defensa]

**Resultado de Ronda**:
- [ ] Idea sobrevivió
- [ ] Idea modificada
- [ ] Idea destruida
- [ ] Se identificó nuevo supuesto

**Aprendizajes**:
[Qué se descubrió en esta ronda]

---

### 📍 Ronda 2: [Tema de Ataque]
[Repetir estructura...]

---

### 📍 Ronda 3: [Tema de Ataque]
[Repetir estructura...]

---

## 4. Supuestos Destruidos / Validados

### ❌ Supuestos Destruidos
| Supuesto | Por qué era falso | Impacto |
|----------|-------------------|---------|
| [Supuesto 1] | [Razón de invalidación] | [Qué cambió por esto] |
| [Supuesto 2] | [Razón de invalidación] | [Qué cambió por esto] |

### ✅ Supuestos Validados
| Supuesto | Evidencia | Confianza |
|----------|-----------|-----------|
| [Supuesto 1] | [Por qué es válido] | Alta/Media/Baja |
| [Supuesto 2] | [Por qué es válido] | Alta/Media/Baja |

---

## 5. Ideas Eliminadas (Graveyard)

### 💀 Feature/Decisión: [Nombre]
**Razón de Eliminación**: [Por qué se rechazó]
**Ahorro Estimado**: [Tiempo/Complejidad evitada]
**Alternativa Adoptada**: [Qué se hizo en su lugar]

### 💀 Feature/Decisión: [Nombre]
[Repetir...]

---

## 6. Propuesta Refinada (Versión Final)

### Stack Validado
- [Tecnología 1] - *Justificación: [razón]*
- [Tecnología 2] - *Justificación: [razón]*

### Arquitectura Final
[Descripción de arquitectura post-debate]

### Features Core (Prioritizadas)
1. **[Feature 1]** - Value Score: [N] - *Por qué: [razón]*
2. **[Feature 2]** - Value Score: [N] - *Por qué: [razón]*
3. **[Feature 3]** - Value Score: [N] - *Por qué: [razón]*

### Features Pospuestas
- [Feature X] - *Razón: [por qué no ahora]*

### Features Eliminadas Permanentemente
- [Feature Y] - *Razón: [valor artificial / complejidad innecesaria]*

---

## 7. Contrato de Fase (Invariantes)

### Reglas Inquebrantables
1. [Regla 1 que NO puede violarse durante implementación]
2. [Regla 2]
3. [Regla 3]

### Límites de Complejidad
- **Complexity Budget**: [X puntos restantes de 100]
- **Max Dependencies**: [N nuevas dependencias permitidas]
- **Max LOC**: [N líneas estimadas]

### Métricas de Éxito
- [Métrica 1]: Baseline: [N], Objetivo: [N]
- [Métrica 2]: Baseline: [N], Objetivo: [N]

### Exit Criteria (¿Cuándo está "done"?)
- [ ] [Criterio 1]
- [ ] [Criterio 2]
- [ ] [Criterio 3]

---

## 8. Metadatos del Debate

### Estadísticas
- **Rondas Totales**: [N]
- **Supuestos Destruidos**: [N]
- **Features Eliminadas**: [N]
- **Ahorro de Complejidad**: [N puntos]
- **Tiempo de Debate**: [X horas]

### Vectores de Ataque Aplicados
- [ ] Contradicción Interna
- [ ] Costo de Oportunidad
- [ ] Complejidad Innecesaria
- [ ] Sesgos Cognitivos
- [ ] Valor Fantasma
- [ ] Premature Optimization
- [ ] Hidden Assumptions
- [ ] Scope Creep Predictivo

### Protocolos Utilizados
- [ ] 5 Whys Agresivo
- [ ] Inversión de Carga
- [ ] Steel Man Attack
- [ ] Constraint Test
- [ ] Failure Pre-Mortem
- [ ] Measurement Challenge
- [ ] Complexity Budget

---

## 9. Próximos Pasos

### Investigación Requerida
- [ ] [Pregunta sin responder 1]
- [ ] [Métrica a medir antes de continuar 2]

### Acciones Inmediatas
1. [Acción concreta 1]
2. [Acción concreta 2]

### Fecha de Revisión
[Fecha para revisar este braindope con nueva información]

---

## 10. Firma del Debate

**Fecha de Convergencia**: [YYYY-MM-DD HH:MM]
**Estado Final**: ✅ CONVERGIDO
**Listo para Implementación**: [Sí/No - Si no, qué falta]

---

## Anexos

### Anexo A: Recursos Consultados
- [Link a documentación técnica relevante]
- [Link a competidor analizado]

### Anexo B: Conversaciones Relevantes
[Enlaces a hilos de Slack, emails, etc. que influenciaron decisiones]

```

---

## Estados del Braindope

### 🔴 En Cuestionamiento
- **Significado**: Debate activo, idea siendo atacada
- **Acciones**: Rondas de ataque en progreso
- **Duración típica**: 1-3 días

### 🟡 Refinando
- **Significado**: Ataques principales superados, puliendo detalles
- **Acciones**: Ajustes menores, documentando aprendizajes
- **Duración típica**: 1-2 días

### ✅ Convergido
- **Significado**: Idea sobrevivió todos los ataques, lista para implementar
- **Acciones**: Genera contrato de fase, comienza desarrollo
- **Congelado**: No se modifica salvo nuevos descubrimientos

### ❌ Abandonado
- **Significado**: Idea destruida completamente, no viable
- **Acciones**: Archivar como referencia de qué NO hacer
- **Valor**: Historia de fracaso rápido y económico

---

## Ejemplos Completos

### Ejemplo 1: Frontend después de API

```markdown
# Braindope: Frontend MVP
**Estado**: ✅ Convergido
**Fecha Inicio**: 2025-01-04
**Fecha Última Actualización**: 2025-01-06
**Participantes**: Usuario (Founder) | Red Team

---

## 1. Contexto de Proyecto

### Estado Actual
- Backend REST API funcionando (Python/FastAPI)
- 12 endpoints core
- Auth con JWT
- Postgres DB
- ~3000 líneas de código backend

### Nueva Fase Propuesta
Construir frontend web para consumir la API.

### Objetivos de la Fase
- Permitir a usuarios interactuar con el sistema sin CLI
- Dashboard básico con métricas
- CRUD de recursos principales

### Restricciones Conocidas
- 1 solo frontend dev (yo)
- Budget: 0 (side project)
- Deadline: 6 semanas

---

## 2. Propuesta Inicial (Versión 0)

### Idea Original
"Voy a usar Next.js 14 con App Router, TypeScript, Tailwind, shadcn/ui, React Query, Zustand para estado global, y Vercel para deploy. También voy a agregar SSR para SEO y maybe internationalization desde el principio."

### Stack/Decisiones Técnicas Propuestas
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui
- React Query
- Zustand
- SSR habilitado
- i18n (react-i18next)
- Vercel

### Supuestos Implícitos (Identificados por Red Team)
- SEO es crítico (¿es app detrás de login?)
- Necesitas estado global complejo (¿cuántas entidades?)
- Multi-idioma es necesario ahora (¿tu target es global?)
- SSR aporta valor (¿qué páginas necesitan pre-renderizar?)

---

## 3. Debate (Rondas de Ataque)

### 📍 Ronda 1: Stack Complexity
**Timestamp**: 14:30

**Red Team ataca**:
"¿Por qué Next.js? Tu app es una SPA detrás de login. No necesitas SSR. ¿O tus usuarios buscan tu dashboard en Google?"

**Usuario responde**:
"Bueno, pensé que SSR es best practice y Next.js es el estándar..."

**Red Team contraataca**:
"'Best practice' sin contexto es cargo cult programming. Define: ¿Qué páginas específicas necesitan SEO? ¿Tienes landing page pública o es 100% dashboard privado?"

**Usuario responde**:
"100% dashboard privado detrás de login... No necesito SEO entonces."

**Resultado de Ronda**:
- [x] Idea modificada
- SSR eliminado → SPA simple es suficiente
- Next.js cuestionado → ¿Qué aporta sobre Vite?

**Aprendizajes**:
- No necesito SSR
- Elegí Next.js por moda, no por necesidad

---

### 📍 Ronda 2: Complexity Budget
**Timestamp**: 14:45

**Red Team ataca**:
"Tu stack propuesto gasta 65/100 puntos de complexity budget antes de escribir una línea:
- Next.js App Router: 25 pts
- TypeScript: 10 pts
- React Query: 15 pts
- Zustand: 10 pts
- i18n: 20 pts

¿Realmente necesitas ese nivel de complejidad para un CRUD básico?"

**Usuario responde**:
"OK, i18n es prematuro. Puedo eliminarlo."

**Red Team contraataca**:
"Bien. ¿Y Zustand? ¿Cuántas entidades de estado compartido tienes? Dame el número exacto."

**Usuario responde**:
"3 entidades: User, Projects, Tasks. Y auth state."

**Red Team contraataca**:
"4 entidades. React Query ya maneja User/Projects/Tasks desde el servidor. Auth state puede ser Context. ¿Por qué Zustand?"

**Usuario responde**:
"...tienes razón. No necesito Zustand si React Query maneja server state."

**Resultado de Ronda**:
- [x] Ideas eliminadas: i18n, Zustand
- Complexity Budget: 65 → 35 puntos
- Stack simplificado significativamente

**Aprendizajes**:
- Estaba agregando complejidad por "completeness" no por necesidad
- React Query + Context es suficiente

---

### 📍 Ronda 3: Framework Choice
**Timestamp**: 15:00

**Red Team ataca**:
"Ahora que eliminaste SSR, i18n y Zustand... ¿qué te da Next.js que Vite + React no te da?"

**Usuario responde**:
"File-based routing, y... bueno, no mucho más."

**Red Team contraataca**:
"File-based routing = 1 feature. 
Vite te da:
- HMR más rápido
- Build time 10x menor
- Configuración más simple
- React Router 6 tiene routing excelente

Next.js sin SSR es como comprar un Tesla para manejar al supermercado. ¿Justificas la complejidad por 1 feature de DX?"

**Usuario responde**:
"No puedo justificarlo. Vite es suficiente."

**Resultado de Ronda**:
- [x] Idea destruida: Next.js
- Adoptado: Vite + React + React Router
- Complexity Budget: 35 → 15 puntos

**Aprendizajes**:
- El "estándar de la industria" no es tu estándar personal
- Evaluar frameworks por lo que USAS, no por lo que TIENEN

---

## 4. Supuestos Destruidos / Validados

### ❌ Supuestos Destruidos
| Supuesto | Por qué era falso | Impacto |
|----------|-------------------|---------|
| "Necesito SSR para SEO" | App es 100% privada detrás de login | Eliminó Next.js |
| "Estado global complejo requiere Zustand" | Solo 4 entidades, React Query + Context suficiente | Eliminó Zustand |
| "i18n debe estar desde día 1" | Target es solo LATAM español, sin demanda multiidioma | Eliminó i18n (20 pts complejidad) |
| "Next.js es obligatorio para apps serias" | Sin SSR, Vite es más simple y rápido | Cambió a Vite |

### ✅ Supuestos Validados
| Supuesto | Evidencia | Confianza |
|----------|-----------|-----------|
| "TypeScript aporta valor" | 3000 LOC backend ya en TS, equipo familiarizado | Alta |
| "React Query simplifica server state" | 12 endpoints, mutations con invalidación compleja | Alta |
| "Tailwind acelera desarrollo" | Experiencia previa, sin diseñador en equipo | Media |

---

## 5. Ideas Eliminadas (Graveyard)

### 💀 Feature: Next.js SSR
**Razón de Eliminación**: App privada no necesita SEO. SSR agrega complejidad sin beneficio.
**Ahorro Estimado**: 25 puntos complejidad, ~20 horas config/debugging
**Alternativa Adoptada**: Vite + React (SPA simple)

### 💀 Feature: Zustand
**Razón de Eliminación**: React Query maneja server state. Context suficiente para auth.
**Ahorro Estimado**: 10 puntos complejidad, 1 dependencia menos
**Alternativa Adoptada**: React Query + Context API

### 💀 Feature: Internationalization (i18n)
**Razón de Eliminación**: Target es solo español LATAM. Sin demanda real de otros idiomas.
**Ahorro Estimado**: 20 puntos complejidad, ~30 horas implementación
**Alternativa Adoptada**: Strings hardcoded en español. i18n se agrega si hay demanda real.

### 💀 Feature: shadcn/ui completo
**Razón de Eliminación**: Solo necesito 5-6 componentes, no 40+.
**Ahorro Estimado**: Bundle size reducido, menos dependencias
**Alternativa Adoptada**: Copy-paste solo componentes que uso

---

## 6. Propuesta Refinada (Versión Final)

### Stack Validado
- **Vite** - *Justificación: HMR rápido, build simple, sin SSR innecesario*
- **React 18** - *Justificación: Familiar, ecosistema maduro*
- **TypeScript** - *Justificación: Consistency con backend, type safety*
- **React Router 6** - *Justificación: Routing client-side, probado*
- **React Query** - *Justificación: 12 endpoints con invalidation compleja*
- **Tailwind CSS** - *Justificación: Rapidez de desarrollo sin diseñador*
- **Componentes selectos de shadcn/ui** - *Justificación: Solo 5-6 componentes necesarios*

### Arquitectura Final
```
src/
├── components/      (componentes UI)
├── features/        (features por módulo)
│   ├── auth/
│   ├── projects/
│   └── tasks/
├── lib/            (utils, api client)
├── hooks/          (custom hooks)
└── routes/         (routing setup)
```

### Features Core (Prioritizadas)
1. **Auth (Login/Register)** - Value Score: 54 - *Blocker total, sin esto no hay app*
2. **Projects CRUD** - Value Score: 48 - *Entidad principal del negocio*
3. **Tasks CRUD** - Value Score: 45 - *Core functionality*
4. **Dashboard básico (3 métricas)** - Value Score: 32 - *Quick overview de valor*
5. **User profile** - Value Score: 20 - *Necesario pero no crítico*

### Features Pospuestas
- **Búsqueda avanzada** - *Razón: Con < 100 items, Ctrl+F es suficiente*
- **Filtros complejos** - *Razón: Agregar cuando haya feedback de usuarios reales*
- **Dark mode** - *Razón: Nice-to-have, no blocker. Usar prefers-color-scheme del OS*

### Features Eliminadas Permanentemente
- **i18n** - *Razón: Target monolingüe, agregar solo si hay demanda real*
- **Real-time updates** - *Razón: Polling cada 30s es suficiente, WebSockets overkill*
- **Advanced analytics** - *Razón: Valor fantasma, nadie lo pidió*

---

## 7. Contrato de Fase (Invariantes)

### Reglas Inquebrantables
1. **Max 5 dependencias frontend nuevas** (ya tenemos: React, React Router, React Query, Tailwind)
2. **No agregar features sin Value Score > 25**
3. **Toda feature debe tener test de integración**
4. **Bundle size < 200KB gzipped**

### Límites de Complejidad
- **Complexity Budget Usado**: 15/100 puntos
- **Max Dependencies**: 5 nuevas (actualmente: 4)
- **Max LOC Estimado**: ~4000 líneas frontend

### Métricas de Éxito
- **Time to Interactive**: Baseline: N/A, Objetivo: < 2s
- **First Contentful Paint**: Baseline: N/A, Objetivo: < 1s
- **Bundle Size**: Baseline: N/A, Objetivo: < 200KB gzipped

### Exit Criteria (¿Cuándo está "done"?)
- [ ] Auth funcional con JWT
- [ ] CRUD completo de Projects
- [ ] CRUD completo de Tasks
- [ ] Dashboard muestra 3 métricas core
- [ ] Tests de integración para flujos críticos
- [ ] Deploy en Vercel (gratis) funcional

---

## 8. Metadatos del Debate

### Estadísticas
- **Rondas Totales**: 3
- **Supuestos Destruidos**: 4
- **Features Eliminadas**: 7
- **Ahorro de Complejidad**: 50 puntos (de 65 → 15)
- **Tiempo de Debate**: 2 horas

### Vectores de Ataque Aplicados
- [x] Complejidad Innecesaria
- [x] Valor Fantasma
- [x] Sesgos Cognitivos (Bandwagon effect)
- [x] Hidden Assumptions

### Protocolos Utilizados
- [x] 5 Whys Agresivo
- [x] Constraint Test (Complexity Budget)
- [x] Steel Man Attack (Next.js)

---

## 9. Próximos Pasos

### Investigación Requerida
- [ ] Evaluar si necesito Optimistic Updates en React Query
- [ ] Decidir estrategia de testing (Vitest + Testing Library)

### Acciones Inmediatas
1. Setup Vite project con TypeScript template
2. Configurar React Router + estructura de carpetas
3. Setup React Query + API client
4. Implementar auth flow (login/register)
5. Deploy inicial a Vercel

### Fecha de Revisión
2025-02-01 (después de 4 semanas de desarrollo)

---

## 10. Firma del Debate

**Fecha de Convergencia**: 2025-01-06 15:30
**Estado Final**: ✅ CONVERGIDO
**Listo para Implementación**: Sí

---

## Anexos

### Anexo A: Recursos Consultados
- [Vite Documentation](https://vitejs.dev)
- [React Query Best Practices](https://tkdodo.eu/blog/practical-react-query)
- [Complexity Budget Article](https://example.com)

### Anexo B: Conversaciones Relevantes
- N/A (solo yo y el red team)
```

---

## Guías de Uso

### Cuándo Crear un Braindope
- ✅ Al iniciar nueva fase importante (frontend, mobile, etc)
- ✅ Al considerar refactor grande
- ✅ Al evaluar cambio de stack/framework
- ✅ Antes de decisiones arquitectónicas mayores

### Cuándo NO Crear un Braindope
- ❌ Features pequeñas (< 1 día de trabajo)
- ❌ Bugs o fixes
- ❌ Mejoras incrementales evidentes
- ❌ Decisiones ya tomadas y funcionando

---

## Versionamiento del Braindope

### Versión 0 (Inicial)
- Propuesta original sin filtro
- Todos los supuestos visibles

### Versión 1-N (Iteraciones)
- Cada ronda de debate modifica el documento
- Se mantiene histórico de ideas eliminadas

### Versión Final (Convergida)
- Contrato de fase congelado
- Solo se modifica si aparece nueva información crítica

---

## Comandos de Manipulación

```bash
# Crea nuevo braindope
redteam init --phase "Frontend MVP" --output braindope-frontend.md

# Agrega ronda de debate
redteam add-round --braindope braindope-frontend.md --topic "Stack Choice"

# Marca como convergido
redteam converge --braindope braindope-frontend.md

# Reabre debate (si encuentras problema post-convergencia)
redteam reopen --braindope braindope-frontend.md --reason "Descubrí que..."

# Genera contrato de fase desde braindope
redteam freeze --input braindope-frontend.md --output phase-contract.md
```

---

## Tips de Calidad

### ✅ Buen Braindope
- Registro honesto del debate completo
- Ideas eliminadas con razón clara
- Aprendizajes explícitos
- Métricas concretas donde sea posible
- Histórico preservado (no borrar rondas)

### ❌ Mal Braindope
- Solo resultado final sin proceso
- Ideas eliminadas sin explicación
- Claims sin justificación
- Editado para "verse bien"
- Rondas eliminadas para ocultar errores

---

## Integración con Git

```bash
# Estructura de carpeta
/docs/braindopes/
├── 2025-01-frontend-mvp.md
├── 2025-02-mobile-app.md
└── 2025-03-api-v2.md

# Commit cada convergencia
git add docs/braindopes/2025-01-frontend-mvp.md
git commit -m "docs: Braindope frontend MVP convergido"

# Tag importantes
git tag -a braindope-frontend-v1 -m "Frontend MVP braindope finalized"
```

---

## Métricas de Éxito del Braindope

- **Completeness**: ¿Tiene todas las secciones obligatorias?
- **Honestidad**: ¿Registra ideas malas eliminadas?
- **Clarity**: ¿Alguien más podría entenderlo en 6 meses?
- **Impact**: ¿Cambió la propuesta significativamente?

**Lema**: *"Un braindope que no elimina ideas es un braindope que no sirvió."*