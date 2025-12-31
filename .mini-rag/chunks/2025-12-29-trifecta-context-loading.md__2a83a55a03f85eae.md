## Checklist Anti-Trampas

✅ **No mezcles data con runtime**: pack no define tools  
✅ **No uses IDs secuenciales**: usa `sha256(title_path_norm + text[:100])`  
✅ **Normaliza `title_path`**: o perderás estabilidad  
✅ **Fallback fence-aware**: o cortarás código  
✅ **Write atomic**: o tendrás JSON corrupto  
✅ **Validador**: o consumirás packs inválidos  

---
