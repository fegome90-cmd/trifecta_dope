No es por performance (sha1 es rápido), sino por estabilidad semántica: un cambio mínimo cambia todo, obvio, pero eso está bien; el problema es que a veces un chunk gigante cambia por una coma y pierdes continuidad total.

✅ Recomendación pragmática:
	•	id_seed = doc + "\n" + title_path + "\n" + sha256(text_normalized)
	•	id = sha1(id_seed)[:10]

Así no dependes de concatenar texto crudo.

3) source_files debe incluir path + sha256 + mtime + size

Con eso puedes:
	•	cachear
	•	detectar cambios
	•	reproducir

4) digest NO debe ser “primeros chars”

En la foto ya dice “resumen estructurado” / “primeras 2 secciones relevantes”. Bien.
Solo asegúrate de que el digest sea pequeño (p. ej. 10–30 líneas por doc) o vuelves a quemar tokens.

5) Falta un campo clave: chunking

Agrega metadatos del método, para que el runtime sepa cómo se generó:

"chunking": { "method": "headings+paragraph_fallback", "max_chars": 6000 }


⸻

Qué haría yo ahora (orden exacto, sin sobre-ingeniería) 🧰

Paso 1 — Implementa el builder (solo pack)
	•	Entrada: 3 .md
	•	Salida: context_pack.json
	•	No metas tools aquí.

Paso 2 — Implementa runtime tool
	•	context.get(chunk_id) → devuelve chunks[].text
	•	(opcional) context.search(query,k) → devuelve IDs usando BM25 simple (o hasta difflib al principio)
