### ⚠️ Limitaciones Identificadas

1. **Búsqueda Lexical Primitiva**
   - Score 0.50 para todos los resultados (no hay ranking real)
   - Requiere refinamiento iterativo de queries
   - No entiende sinonimia (ej: "test" vs "pytest" vs "verification")

2. **Sin Deduplicación**
   - `skill.md` aparece 2 veces en chunks (skill:773705da1d, ref:skill.md:ce2488eaa2)
   - Consume 1.770 tokens duplicados (12% del total)

3. **README.md Domina el Índice**
   - 42% de tokens en 1 chunk
   - Podría fragmentarse en secciones

4. **Índice Flat (Sin Jerarquía)**
   - Todos los chunks de igual "peso" en búsqueda
   - No hay noción de "core" vs "reference"

---
