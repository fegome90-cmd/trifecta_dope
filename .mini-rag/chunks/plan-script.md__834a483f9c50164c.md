⸻

Ajuste recomendado al schema (mínimo, no inflar)

Tu schema está casi listo. Yo solo haría estos ajustes:
	•	chunking.method: "headings+paragraph_fallback+fence_aware"
	•	digest: cambiar summary por algo estructurado:
	•	bullets: [] o text + source_chunk_ids: []
	•	index.title_path: ok como lista ✅
	•	chunks.title_path: ok ✅
	•	chunks: añade source_path, heading_level, char_count

⸻

Plan de implementación (orden correcto, sin humo) 🧪

Fase 1 (MVP: hoy)
	1.	Generar context_pack.json v1 con:
	•	fence-aware headings
	•	chunking + fallback
	•	digest determinista (score)
	•	IDs estables con normalización
	2.	Tests:
	•	snapshot (mismo input => mismo output)
	•	stability (cambio en doc A no cambia IDs de doc B)

Fase 2 (cuando duela el tamaño)
	3.	Implementar context.db (SQLite aislado por proyecto)
	4.	get_context y search_context desde DB

⸻

Veredicto

Sí, esto está bien. Pero si implementas tal cual sin los fixes de normalización/digest/fence-aware/metadata, vas a tener un sistema que “funciona” y luego se vuelve inestable y lento.

Siguiente paso lógico: implementa Fase 1 + 2 tests, y recién después te das el lujo de SQLite. 🚀
