T del Hito 1.
Hito 3: Edición Segura (Shadow Workspace)
Objetivo: Edición atómica y validada.
Entregables:
Sistema de Archivos Virtual (VFS) sincronizado con LSP (didChange).
Herramienta verify_edit(file, new_content): Envía cambio al VFS, espera diagnósticos, retorna errores o OK.
Integración de Selectores Semánticos para aplicar ediciones (apply_edit(selector, new_code)).
DoD: El agente intenta aplicar código con error de sintaxis; el sistema devuelve el error del compilador sin modificar el disco.
6. Riesgos Críticos y Estrategias de Mitigación
La implementación conlleva riesgos técnicos significativos que deben ser gestionados proactivamente.
Riesgo Crítico
Impacto
Mitigación Concreta
1. Latencia de Cold Start (LSP)
Bloqueo del agente por >30s al abrir repos grandes.
Estrategia Híbrida: Usar Tree-sitter (inmediato) para las primeras interacciones. Cargar LSP en background. Informar al usuario "Analizando en profundidad..." sin bloquear.
2. Code Drift (Desincronización)
El agente edita líneas incorrectas tras cambios previos.
Selectores Semánticos: Prohibir referencias por número de línea en comandos de edición. Usar identificadores lógicos o anclajes de contenido (contexto de 3 líneas arriba/abajo).
3. Resource Bloat (Memoria)
Colapso del sistema al abrir múltiples servidores LSP (Java + JS + Python).
Gestión de Recursos Activa: Limitar a 1 servidor activo a la vez si la RA
