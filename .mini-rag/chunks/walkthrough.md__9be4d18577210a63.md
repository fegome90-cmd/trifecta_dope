## T5 — session.md contract + watcher thin
**Objetivo**: Documentar el contrato de Autopilot para referencia humana (v1) o futura implementación (v2).

- **Archivos tocados**:
  - `src/application/use_cases.py` (Solo soporte básico, sin motor de lectura de configs).
- **Cambios concretos**:
  - **Runner Externo (Watcher)**: Dispara `trifecta ctx sync` ante cambios (ej: `fswatch -o . | xargs -n1 -I{} trifecta ctx sync --segment .`).
  - **Motor Interno**: NO hay un motor de lectura de configuración en v1. La lógica es fija.
