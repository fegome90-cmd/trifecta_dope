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
