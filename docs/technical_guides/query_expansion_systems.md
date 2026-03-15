# Query Expansion Systems

## Overview

Trifecta tiene **dos sistemas independientes** de expansión de queries:

1. **Linter Expansion** - Controlada por TRIFECTA_LINT
2. **Spanish Alias Expansion** - Siempre activa (condicional)

## Linter Expansion

### Trigger
- Queries vagas (1-2 tokens)
- Flag `TRIFECTA_LINT=1` o `--lint`

### Implementación
- Archivo: `src/domain/query_linter.py`
- Usa: `anchors.yaml` para expandir términos vagos

### Comportamiento A/B
- **OFF**: Query pasa sin modificación
- **ON**: Se añaden anchors strong/weak según clasificación

## Spanish Alias Expansion

### Trigger
- Query detectada como español
- Primera pasada (pass 1) retorna 0 hits
- No es fixture (`source != "fixture"`)

### Implementación
- Archivo: `src/application/spanish_aliases.py`
- Diccionario: `SPANISH_ALIASES` (español → inglés)
- Detección: `detect_spanish()` - caracteres, stopwords, aliases

### Comportamiento
```python
# Two-pass search en search_get_usecases.py:355-414
if len(final_hits) == 0 and detect_spanish(query):
    spanish_alias_variants = expand_with_spanish_aliases(query)
    # Re-intentar búsqueda con variantes en inglés
```

## Interacción entre Sistemas

### Caso Problemático (Resuelto)
```python
# Query: "servicio"
# LINT=OFF, pero Spanish Expansion activa:
#   "servicio" → "service"
#   "service" coincide con "ContextService" en chunk
# Resultado: 1 hit (inesperado si se esperaban 0)
```

### Solución
Usar queries que no triggeran Spanish Expansion:
- Evitar palabras en `SPANISH_ALIASES`
- Evitar caracteres españoles (áéíóúñ)
- Evitar stopwords españolas

Ejemplo: `"xyznonexistent"` no triggera ninguna expansión.

## Testing A/B Controlado

Para testear SOLO Linter Expansion:
1. No usar aliases.yaml (usa anchors.yaml)
2. No usar queries españolas
3. Usar queries vagas (1-2 tokens) en inglés

Ver: `tests/integration/test_ctx_search_linter_ab_controlled.py`
