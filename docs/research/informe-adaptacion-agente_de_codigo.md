# Informe: Paquetes adaptables desde agente_de_codigo

## Contexto

Este informe resume componentes en ` /Users/felipe_gonzalez/Developer/agente_de_codigo/packages` que pueden adaptarse a `trifecta_dope`, con enfoque en el roadmap actual (context packs, progressive disclosure, runtime de almacenamiento).

## Candidatos directos (Python)

### 1) MemTech (almacenamiento multi-tier)

- Ubicacion: ` /Users/felipe_gonzalez/Developer/agente_de_codigo/packages/memtech/manager.py`
- Complementos: ` /Users/felipe_gonzalez/Developer/agente_de_codigo/packages/memtech/storage_l0.py`
- Complementos: ` /Users/felipe_gonzalez/Developer/agente_de_codigo/packages/memtech/storage_l1.py`
- Complementos: ` /Users/felipe_gonzalez/Developer/agente_de_codigo/packages/memtech/storage_l2.py`
- Complementos: ` /Users/felipe_gonzalez/Developer/agente_de_codigo/packages/memtech/storage_l3.py`

Hallazgos:
- Orquesta almacenamiento L0 (local), L1 (cache), L2 (PostgreSQL), L3 (Chroma).
- Soporta TTL, metricas de uso y fallback por capa.
- Tiene configuracion unificada con un adaptador (config_adapter).

Adaptacion sugerida:
- Usarlo como base para el runtime de context packs (L0/L1) y luego L2 (SQLite) en `trifecta_dope`.
- Reemplazar L2 PostgreSQL por SQLite y retirar L3 si no se usa vector search.

Riesgos:
- Dependencias externas si se mantiene L2 Postgres o L3 Chroma.
- Cambios de configuracion para alinear con `trifecta_dope` (paths, naming, manejo de errores).

### 2) Agentes de calidad/seguridad

- Calidad: ` /Users/felipe_gonzalez/Developer/agente_de_codigo/packages/agents/quality_agent.py`
- Seguridad: ` /Users/felipe_gonzalez/Developer/agente_de_codigo/packages/agents/security_agent.py`

Hallazgos:
- Pipelines de analisis que generan SARIF 2.1.0.
- Ejecutan herramientas externas (ruff, eslint, lizard, semgrep, gitleaks, osv-scanner).
- Normalizan errores y generan reportes resumen.

Adaptacion sugerida:
- Integrarlos como etapa opcional en `validate` o como comando `scan` para enriquecer el `session_*.md` o el context pack.

Riesgos:
- Dependencias de herramientas CLI externas.
- Tiempo de ejecucion y requerimientos de instalacion.

## Candidatos conceptuales (TypeScript -> Python)

### 3) Tool Registry

- Fuente: ` /Users/felipe_gonzalez/Developer/agente_de_codigo/packages/shared/src/tool-registry/tool-registry.ts`

Hallazgos:
- Registro central de herramientas con validacion (zod), metricas y control de ejecucion.

Adaptacion sugerida:
- Implementar una version ligera en Python para el futuro MCP Discovery Tool.

Riesgos:
- Reescritura completa en Python.
- Definir un esquema de configuracion y validacion compatible.

### 4) Supervisor / Routing

- Fuente: ` /Users/felipe_gonzalez/Developer/agente_de_codigo/packages/supervisor-agent/README.md`

Hallazgos:
- Modelo de validacion de agentes, routing y prioridad con fallback.

Adaptacion sugerida:
- Usar el enfoque para decidir a que contexto o pack acceder segun senales del repo.

Riesgos:
- No hay implementacion Python directa; requiere diseno nuevo.

## Fit con el roadmap de Trifecta

- Context packs grandes: MemTech es el candidato mas directo.
- MCP discovery: Tool Registry es el patron mas claro.
- Progressive disclosure: modelo de routing/validacion del supervisor puede orientar el selector de nivel L0/L1/L2.

## Dependencias a considerar

- Herramientas CLI externas (semgrep, gitleaks, osv-scanner, ruff, eslint, lizard).
- Drivers o clientes (PostgreSQL, Chroma) si se mantiene L2/L3 en MemTech.

## Recomendacion inicial

Priorizar MemTech para cubrir el runtime de almacenamiento y caching de context packs. En paralelo, definir una interfaz minima para discovery de herramientas y progresive disclosure, inspirada en Tool Registry y Supervisor, pero ligera y en Python.

## Siguientes pasos sugeridos

1) Decidir si el runtime de context packs requiere solo L0/L1 o L2 (SQLite).
2) Definir si la validacion de calidad/seguridad sera parte del pipeline por defecto o solo bajo flag.
3) Si quieres, puedo mapear un plan de port de MemTech a un modulo `trifecta_dope/src/infrastructure/storage/`.
