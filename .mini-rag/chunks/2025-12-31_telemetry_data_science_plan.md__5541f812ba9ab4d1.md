### Best Practices de CLI Telemetry

**Fuente**: [6 telemetry best practices for CLI tools - Massimiliano Marcon](https://marcon.me/articles/cli-telemetry-best-practices/)

1. **Be intencional** - Tracking plan defining exactamente qué capturar
2. **Transparencia** - Mostrar cómo deshabilitar telemetry
3. **Múltiples formas de opt-out** - Commands, env vars, config files
4. **Performance first** - Best-effort sending con timeouts
5. **Environment data** - OS, Docker usage para platform decisions
6. **High volume prep** - Scripting y CI generan muchos eventos
