Veredicto (duro y útil)
	•	El enfoque 3 capas: ✅ correcto.
	•	Decir “no hay riesgo”: ❌ error de criterio (aunque el riesgo sea bajo).
	•	digest por “primeros 800 chars”: ❌ mala calidad semántica.
	•	Definir tools dentro del pack: ❌ acoplamiento innecesario.
	•	Falta versionado + IDs estables: ❌ te va a doler en 2 semanas.

Si aplicas solo 3 fixes hoy:
	1.	schema_version + manifest,
	2.	IDs determinísticos por hash,
	3.	tool fuera del pack,
ya pasas de “experimento” a “contrato serio” 🚀

Sí: ahora sí está en forma “contrato serio” ✅🧱

En la foto ya se ve que el agente corrigió exactamente los 3 puntos críticos:
	•	schema_version + created_at + generator_version + source_files → ya hay contrato y trazabilidad.
	•	IDs determinísticos por hash (sha1(title_path + text)[:10]) → estabilidad real.
	•	Tool fuera del pack (“solo data”) → desacoplamiento correcto.

Eso es un GO para implementar.

⸻

Pero antes de “merge mental”: 5 checks que NO puedes saltarte ⚠️

1) title_path debe ser estable y normalizado

Si title_path cambia por detalles (espacios, mayúsculas, emojis, etc.), los IDs cambian aunque el contenido sea el mismo.

Regla mínima:
	•	trim
	•	colapsar espacios
	•	lower() opcional (yo lo haría)
	•	separador fijo (/)

2) Hash: evita “hash de texto completo” si el chunk puede ser grande
