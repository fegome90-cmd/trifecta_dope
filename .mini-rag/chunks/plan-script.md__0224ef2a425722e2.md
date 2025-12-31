Como esto es plumbing + IO + JSON:
	•	Python ✅ si quieres velocidad de implementación y scripts rápidos.
	•	TypeScript/Node ✅ si tu runtime de agentes ya está en Node (Trifecta/SkillFabrik/CLI).
	•	Go/Rust solo si lo vas a convertir en componente core de alto rendimiento.

Mi recomendación: si tus agentes están en Python hoy → Python. Si HemDov/Trifecta vive en Node → TS.

⸻

4) Implementación mínima en Python (pack builder) 🧰

Esto genera:
	•	context_pack.json con digest, índice y chunks.
	•	Luego tu agente mete en el prompt solo digest + index.
