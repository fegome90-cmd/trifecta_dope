✅ Regla simple:
	•	Recorres líneas y mantén in_fence = False
	•	Si una línea empieza con ``` o ~~~: toggle in_fence
	•	Ignora headings mientras in_fence == True

Eso evita partir secciones por # dentro de bloques de código.

⸻

4) El context_pack.json puede volverse enorme → necesitas límites

Si más adelante metes docs grandes, meter todos los chunks con texto en un JSON único puede ser pesado (IO y memoria).

✅ Política pragmática:
	•	En v1: ok tener chunks con texto (simple).
	•	Pero deja listo el salto a v2-lite:
	•	index + chunks_meta en JSON
	•	textos en SQLite (context.db) o en archivos chunks/<id>.md

Tu plan ya menciona SQLite por proyecto: perfecto, pero no intentes hacerlo todo ahora. Hazlo fase 2.

⸻

5) Falta metadata útil para debugging y retrieval

Tu schema v1 está bien, pero le faltan campos que te van a ahorrar horas:

✅ Añade a index[] o chunks[]:
	•	source_path
	•	heading_level
	•	char_count
	•	line_count
	•	start_line, end_line (si lo puedes calcular)

Eso permite: “muéstrame chunk X y de dónde salió”.

⸻

6) get_context lineal buscando en lista = ok para 30 chunks, malo para 3000

Tu ejemplo hace loop por pack["chunks"]. Para MVP sirve, pero en runtime serio debe ser O(1).

✅ Solución mínima sin DB:
	•	al cargar el pack, construye un dict {id: chunk} en memoria

✅ Solución pro:
	•	context.db con chunks(id PRIMARY KEY, text, doc, title_path, …) + índice.
