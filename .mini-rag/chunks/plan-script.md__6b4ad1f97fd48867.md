1) Tu definición de Digest es demasiado “manual”

“Primeras 2 secciones relevantes (no Overview vacío…)”

Eso suena bien, pero si no lo defines como regla reproducible, el digest será inconsistente.

✅ Regla reproducible (MVP, determinista):
	•	Construye un ranking de secciones por score:
	•	+3 si title contiene keywords: core, rules, workflow, commands, usage, setup, api, architecture
	•	+2 si level == 1 o 2
	•	−2 si title contiene overview, intro y el texto es corto (ej < 300 chars)
	•	Toma top-2 chunks por doc, con límite de N chars total (ej: 1200 por doc)

Así el digest siempre sale igual con el mismo input.

⸻

2) ID estable: normaliza o vas a tener IDs que cambian por tonteras

Tu fórmula sha1(title_path + text) está bien solo si normalizas:

✅ Normalización mínima:
	•	title_path: trim + colapsar espacios + opcional lower()
	•	text: normalizar \r\n → \n, colapsar whitespace extremo, y no tocar contenido dentro de code fences (para no “mutar” código)

Si no, cambiar un doble espacio o un emoji en un heading te cambia el ID aunque el contenido lógico sea el mismo.

Bonus: incluye doc + "\n" + "\x1f".join(title_path) + "\n" + text_hash en vez de concatenar texto crudo.

⸻

3) “Code fence safety” no es un checkbox: es un bug factory si lo implementas a medias

Tu regla “no chunkear adentro” es correcta, pero debes implementarla como estado:
