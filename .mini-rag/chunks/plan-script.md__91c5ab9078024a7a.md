Perfecto. “Cargar 3 archivos de contexto a los agentes” puede significar dos cosas muy distintas, y si eliges mal, vas a quemar tokens como si fueran leña 🔥:

1) Dos formas de “cargar contexto” (una es cara, la otra es la correcta)

A) Inyectar los 3 markdown completos en el prompt
	•	✅ Simple
	•	❌ Carísimo en tokens en cada llamada
	•	❌ Escala pésimo (hoy son 3, mañana son 30)

Esto solo sirve si haces muy pocas llamadas o si tu proveedor tiene prompt caching real (no siempre disponible; en local casi nunca).

B) Contexto “siempre” = resumen + índice; texto completo = bajo demanda
	•	✅ Bajo consumo de tokens
	•	✅ Escala bien
	•	✅ Más robusto: el agente pide solo lo que necesita (tool o retrieval local)

Este es el estándar serio para agentes.

⸻

2) Diseño recomendado (pragmático y barato)

Vas a construir un Context Pack con 3 capas:
	1.	Digest fijo (siempre en el prompt)
	•	10–30 líneas por archivo: propósito, conceptos clave, definiciones.
	2.	Índice de secciones (siempre en el prompt)
	•	Lista de chunk_id → título → 1 línea preview.
	3.	Chunks completos (NO van al prompt)
	•	Se entregan vía tool: get_context(chunk_id) o search_context(query).

Con eso, tu agente trabaja “con memoria” sin pagar el costo de mandar todo siempre.

⸻

3) ¿Qué lenguaje usar?
