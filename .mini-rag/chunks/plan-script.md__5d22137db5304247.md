4) Tu lista de fases: el agente está sobre-planificando (un poco) 🧯

En la captura aparecen fases tipo:
	•	validaciones, help con ejemplos, dry-run, completions fish, mejorar templates, E2E, README, etc.

Eso está bien… pero no ahora.

Tu “MVP real” para cargar contexto a agentes debería ser:

MVP (en orden)
	1.	Generar context_pack.json v1 (schema versionado)
	2.	Implementar tool runtime: context.get(id) + opcional context.search(query)
	3.	Integración mínima: agente recibe digest+index y solo pide chunks cuando necesita
	4.	Tests: snapshot del pack + test de estabilidad IDs

Lo demás (completions, README bonito, etc.) viene después.

⸻

5) Recomendación concreta: cómo ajustaría tu contrato (sin inflarte el scope) 🧩

context_pack.json (contrato mínimo bueno)
	•	schema_version
	•	segment (ok)
	•	docs[] con hash y stats
	•	digest[] (pero generado con reglas decentes)
	•	index[] con id, doc, title_path, preview, token_est
	•	chunks[] con id, title_path, text

Runtime tool (separado)
	•	get_context(id) → devuelve texto del chunk
	•	search_context(query, k) → devuelve IDs (BM25 simple al inicio)

⸻
