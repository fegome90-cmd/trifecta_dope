B) “Tool get_context definida en el mismo output” → mala separación de responsabilidades

Un pack de contexto es data, una tool es runtime.

Si mezclas ambas:
	•	el pack deja de ser portable,
	•	cambias el runtime y rompes el pack (o viceversa),
	•	terminas con “pack que pretende dictar herramientas” (riesgo de seguridad y de control).

✅ Mejor: el context_pack.json solo data + metadatos.
La tool vive en tu runtime (HemDov/Trifecta), y el pack solo provee IDs.

⸻

C) Falta un schema_version y un manifest

Sin esto, no hay contrato.

✅ Mínimo:
	•	schema_version: 1
	•	created_at
	•	generator_version
	•	source_files: [{path, sha256, mtime}]
	•	chunking: {method, max_chars}

⸻

D) IDs tipo skill:0001 no son estables ante cambios

Si insertas un heading arriba, cambia la numeración y rompes referencias.

✅ Mejor: IDs determinísticos por hash:
	•	id = doc + ":" + sha1(normalized_heading_path + chunk_text)[:10]
Así, si no cambia el chunk, el ID no cambia.

⸻

E) Chunking por headings: cuidado con código, tablas, y bloques largos

Tree-sitter / markdown-it no es obligatorio, pero hay que vigilar:
	•	headings dentro de code fences,
	•	secciones gigantes sin headings,
	•	tablas largas.

✅ Solución pragmática: fallback por párrafos si excede max_chars (esto el plan ya lo menciona; perfecto) pero asegúrate de respetar code fences.

⸻
