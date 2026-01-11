**Rationale de descarte** (braindope:L391-L400):
> ### 💀 Feature: Auto-detección de Tool Use  
> **Razón de Eliminación**: No es necesaria, metadata es manual (flags existentes)  
> **Ahorro Estimado**: ~15 horas de parser complejo  
> **Alternativa Adoptada**: Flags `--files` y `--commands` (ya existen)
>
> ### 💀 Arquitectura: session_journal.jsonl separado  
> **Razón de Eliminación**: Usuario decidió reutilizar telemetry (no reinventar rueda)  
> **Ahorro Estimado**: ~10 horas (evita JSONL writer duplicado)  
> **Alternativa Adoptada**: Event type `session.entry` en telemetry existente

---
