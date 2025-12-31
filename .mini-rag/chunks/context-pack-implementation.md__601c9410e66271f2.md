### Propiedades de Estabilidad

| Cambio en contenido | ¿Cambia ID? | Por qué |
|---------------------|-------------|---------|
| Mismo texto, mismo título | ❌ No | Mismo seed → mismo hash |
| Texto modificado | ✅ Sí | `text_hash` cambia |
| Whitespace en título | ❌ No | `normalize_title_path()` elimina |
| Case en título | ❌ No | `lower()` en normalización |
| Cambio en otro doc | ❌ No | ID incluye `doc` como prefijo |
