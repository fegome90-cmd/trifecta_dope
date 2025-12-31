# 3) Segment Contract Header

Todos los archivos de la trifecta llevan este header de 5-8 líneas:

```yaml
---
segment: <nombre-del-segmento>
scope: <descripción corta del alcance>
repo_root: <path absoluto a la raíz del repo>
last_verified: YYYY-MM-DD
depends_on:  # Archivos que invalidan esta trifecta si cambian
  - path/to/critical_file.py
---
```

---
