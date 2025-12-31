### Componentes Principales

| Componente | Responsabilidad |
|------------|-----------------|
| `normalize_markdown()` | Estandarizar formato (CRLF → LF, collapse blank lines) |
| `chunk_by_headings_fence_aware()` | Dividir en chunks respetando code fences |
| `generate_chunk_id()` | Crear IDs estables via hash |
| `score_chunk()` | Puntuar chunks para digest |
| `ContextPackBuilder` | Orquestar generación completa |

---
