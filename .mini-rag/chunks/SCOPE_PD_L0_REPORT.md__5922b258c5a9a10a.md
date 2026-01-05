### 2. ¿Noción de niveles (L0/L1/L2)?
- **Documentada**: El `README.md` (L112-116) define umbrales de Score (`<0.6 L0`, etc.).
- **Real (Código)**: `ContextService` no usa los umbrales de score todavía. Implementa PD mediante:
  - `mode="excerpt"`: Primeras 25 líneas (`L1` parcial).
  - `mode="skeleton"`: Estructura (`L0` técnico).
  - `mode="raw"`: Contenido total con guardrail de presupuesto.
