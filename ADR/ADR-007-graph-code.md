# ADR-007: Trifecta Graph como capa semántica CLI-first

## Status

Approved

## Date

2026-03-13

## Context

Trifecta ya posee o está construyendo piezas para análisis estructural del código, en particular AST como base topológica y LSP como capa de resolución fina. Al mismo tiempo, surgió la posibilidad de tomar ideas de sistemas como CodeGraphContext para mejorar navegación, impacto y recuperación estructural.

El riesgo identificado es caer en uno de estos errores:
- tratar MCP como núcleo cuando en realidad solo es un protocolo de exposición;
- duplicar AST o LSP;
- convertir el grafo en un generador de contexto textual para prompts;
- inflar la arquitectura con complejidad que no calza con el modelo meta-first / PCC de Trifecta.

## Decision

Se adopta la siguiente decisión arquitectónica:

Trifecta Graph será una capa semántica local, CLI-first, persistida en SQLite, integrada dentro del binario trifecta, que consume AST como sensor base y LSP como enriquecimiento opcional.

### Principios rectores

1. **AST es el mapa; LSP es el GPS.**
   No compiten. AST define topología; LSP mejora precisión.
2. **PCC sigue siendo el mecanismo de recuperación.**
   El grafo no empuja contexto al prompt. Aporta señal navegacional para decidir mejores invocaciones.
3. **CLI es el core.**
   MCP no forma parte del núcleo. Solo podría existir más adelante como adaptador externo.
4. **SQLite es el store inicial.**
   No se usará GraphDB externa ni VectorDB como núcleo en esta etapa.
5. **No se duplican sensores existentes.**
   El nuevo subsistema consume AST/LSP; no los reemplaza ni los reimplementa.

### Alcance

Trifecta Graph tendrá como objetivo inicial:
- indexar símbolos y relaciones estructurales;
- persistir un grafo local por segmento;
- responder consultas de búsqueda estructural;
- responder callers, callees, neighbors e impact;
- enriquecer el ranking y la navegación dentro del flujo PCC.

### No objetivos

Quedan explícitamente fuera del alcance inicial:
- generar prompts o bloques textuales densos para el LLM;
- reemplazar ctx build, ctx search o ctx.get;
- introducir MCP como dependencia central;
- introducir Neo4j, Kuzu o infra de servicio remoto;
- reimplementar parsers AST o resolución LSP;
- construir visualizadores complejos o sistemas asíncronos pesados.

### Superficie CLI aprobada

El namespace base será:
- `trifecta graph index`
- `trifecta graph status`
- `trifecta graph search`
- `trifecta graph callers`
- `trifecta graph callees`
- `trifecta graph impact`

Más adelante podrán entrar:
- `trifecta graph neighbors`
- `trifecta graph sync-links`
- `trifecta audit dead-code`
- `trifecta audit cycles`
- `trifecta watch ...`

## Modelo operativo

### Entradas

- AST adapter con contrato JSON estable
- LSP adapter opcional
- metadata de segmento / SegmentRef SSOT
- Context Pack, cuando exista

### Pipeline

```
AST/LSP → normalización → IR semántico → SQLite graph store → query engine → señal para PCC
```

### Salidas

Los comandos del grafo deben soportar:
- modo machine para agentes
- modo explain para humanos/debug
- modo both cuando se necesiten ambos

## Contratos obligatorios

### 1. Identidad canónica de símbolos

Los IDs de símbolos deben construirse sin depender de líneas.
Base aprobada:

```
repo + segment + lenguaje + path normalizado + symbol_path + signature_hash
```

No se acepta `sha256(qualified_name)` como contrato suficiente.

### 2. Modelo de relaciones

Las relaciones deben incluir al menos:
- kind
- provenance
- confidence
- reason_code
- observed_at
- indexed_at
- evidence_ref

No se acepta `uncertain=True` como único modelo de incertidumbre.

### 3. Boundary graph ↔ context pack

El vínculo símbolo ↔ chunk es un contrato formal.
Debe existir política explícita para:
- links válidos,
- links stale,
- chunks fantasma,
- reconciliación,
- invalidación por cambio de context pack.

### 4. Frescura

La frescura será event-based, no TTL-based.
Debe existir `graph status` como fuente de verdad del estado:
- absent
- fresh
- stale_files
- stale_links
- links_absent
- corrupt

## Estrategia de madurez

### MVP

- AST-only
- SQLite
- IDs canónicos
- graph index
- graph status
- graph search

### Fase operativa

- callers
- callees
- impact
- indexado incremental
- modelo de relaciones con confidence/provenance

### Fase de integración PCC

- links símbolo ↔ chunk
- sync-links
- señal al ranking PCC
- outputs duales machine/explain

### Fase posterior

- enriquecimiento LSP real
- auditorías
- watch
- eventual adaptador MCP

## Consequences

### Positivas

- mantiene el minimalismo deliberado de Trifecta;
- mejora navegación estructural sin romper PCC;
- evita sobreingeniería prematura;
- deja una base auditable y portable;
- separa sensores, persistencia y consulta con claridad.

### Negativas

- el MVP no tendrá precisión semántica completa;
- AST-only producirá relaciones heurísticas;
- sin sync-links, el grafo no podrá entregar chunk IDs confiables;
- algunas capacidades avanzadas dependerán de la maduración real de LSP.

## Decision Final

No se portará CodeGraphContext como producto.
Se extraerá su valor conceptual y se implementará una proyección de grafo sobria, local y auditable dentro de Trifecta.
AST entra primero. LSP enriquece después. PCC sigue mandando.
