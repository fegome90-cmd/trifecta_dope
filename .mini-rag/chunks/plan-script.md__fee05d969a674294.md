Aunque sea nuevo y sin usuarios, sí hay riesgos reales:
	•	Riesgo de integración: puede que ya haya otro componente esperando el formato actual (aunque sea “solo tú”). El costo no es “usuarios”, es dependencias.
	•	Riesgo de diseño temprano: si cambias el esquema sin versionarlo, cuando mañana agregues caching/RAG/skills vas a terminar con “formato v0 fantasma”.
	•	Riesgo de deuda: “lo cambio directo” suele terminar en “nadie sabe cuál es el contrato”. Un agente sin contrato = caos.

✅ Lo correcto no es “no hay riesgo”, es: riesgo bajo, pero versiona el contrato desde ya.

⸻

2) Lo bueno del plan (esto sí está bien) ✅
	•	3 capas (digest/index/chunks) → es el patrón correcto para bajar tokens.
	•	Chunking por headings → simple, interpretable, debuggable.
	•	Preview corto en el índice → ayuda al LLM a elegir sin meter todo.
	•	Eliminar formatos duplicados (compact/json/yaml) → menos superficie de bugs.

Hasta ahí: bien.

⸻

3) Lo flojo / frágil del diseño (aquí se rompe en producción) 🔧

A) digest = primeros 800 chars es malo como “memoria”

Eso es básicamente “lo que estaba arriba”, no “lo importante”.

Fallo típico: el archivo empieza con prólogo y advertencias, y el digest queda inútil.

✅ Mejor: digest debe ser resumen estructurado (bullet points + glosario) o al menos “primeras 2 secciones relevantes”, no “primeros caracteres”.

⸻
