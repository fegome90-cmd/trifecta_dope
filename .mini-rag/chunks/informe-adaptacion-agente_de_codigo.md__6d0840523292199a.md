### 2) Agentes de calidad/seguridad

- Calidad: ` /Users/felipe_gonzalez/Developer/agente_de_codigo/packages/agents/quality_agent.py`
- Seguridad: ` /Users/felipe_gonzalez/Developer/agente_de_codigo/packages/agents/security_agent.py`

Hallazgos:
- Pipelines de analisis que generan SARIF 2.1.0.
- Ejecutan herramientas externas (ruff, eslint, lizard, semgrep, gitleaks, osv-scanner).
- Normalizan errores y generan reportes resumen.

Adaptacion sugerida:
- Integrarlos como etapa opcional en `validate` o como comando `scan` para enriquecer el `session_*.md` o el context pack.

Riesgos:
- Dependencias de herramientas CLI externas.
- Tiempo de ejecucion y requerimientos de instalacion.
