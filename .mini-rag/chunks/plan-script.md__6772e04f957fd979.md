Tu runtime expone una función tipo:
	•	get_context(chunk_id) -> text
	•	opcional: search_context(query) -> top chunk_ids

Eso hace que el agente “tenga” los 3 archivos sin que tú pagues por enviarlos completos en cada interacción.

⸻

6) Errores típicos (que te harían perder el objetivo)
	•	“Metamos todo al system prompt y listo” → funciona, pero pagas siempre.
	•	“Resumen automático gigante” → es otro prompt caro disfrazado.
	•	“RAG sin índice” → el agente no sabe qué hay y pide cosas a ciegas (más llamadas, más costo).

⸻

Siguiente paso lógico (sin preguntas, directo)

Implementa el Context Pack + una tool get_context. Después, si quieres aún menos tokens:
	•	agrega un search_context(query) local (BM25/mini-embeddings),
	•	y el agente casi nunca pedirá chunks grandes.

Lo que muestra la captura (y por qué importa) 🧠🧱

Veo un agente proponiendo reemplazar el script actual por un “Context Pack” de 3 capas (digest + index + chunks) y además “definir la tool get_context en el mismo output”. También afirma: “No hay riesgo: el script es nuevo, sin commit, sin usuarios”.

Eso último es una conclusión peligrosa (aunque el riesgo sea bajo). Y el diseño tiene partes buenas y otras que te van a explotar cuando lo conectes a agentes reales.

⸻

1) “No hay riesgo” → Incorrecto (riesgo bajo ≠ riesgo cero) ⚠️
