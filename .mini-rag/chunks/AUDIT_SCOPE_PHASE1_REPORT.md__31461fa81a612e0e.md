## F) Preguntas Bloqueantes (Máx 3)

**P1**: ¿Cuál es la SSOT definitiva para `ContextPack`?
- **Opción A**: `src/domain/context_models.py:39-48` (Pydantic)
- **Opción B**: `src/domain/models.py:100-105` (dataclass)
- **Impacto**: Si se elige A, hay que eliminar B y migrar todos los usos. Viceversa.

**P2**: ¿Debe `segment_id` ser derivado del path (SHA256) o del segment name?
- **Actual**: `compute_segment_id()` usa SHA256 del path absoluto
- **Alternativo**: `normalize_segment_id()` normaliza el nombre del segment
- **Impacto**: Si el repo se mueve de ubicación, el SHA256 cambia pero el nombre no.

**P3**: ¿Cuál es el mecanismo de lock único para el proyecto?
- **Opción A**: `fcntl.lockf` (usado en LSP daemon)
- **Opción B**: `flock` (usado en file_system_utils)
- **Impacto**: Consistencia y previsibilidad de comportamiento.

---
