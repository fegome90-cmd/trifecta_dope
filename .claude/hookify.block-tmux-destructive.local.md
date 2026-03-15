---
name: block-tmux-destructive
enabled: true
event: bash
pattern: tmux\s+(kill-server|kill-session\s+(-a|--all))
action: block
---

**PROTECCION DE TMUX ACTIVADA**

Estás intentando ejecutar un comando destructivo de tmux:
- `tmux kill-server` - Mata TODAS las sesiones tmux
- `tmux kill-session -a` - Mata todas las sesiones excepto la actual

**REGla personal del usuario:**
> "CRÍTICO: Pérdida de Trabajo por Cierre de Sesiones Tmux" - Incidente 2025-12-31
> Trabajo perdido cuando se cerraron sesiones de tmux

**Acciones permitidas:**
- `tmux kill-session -t nombre` - Mata una sesión específica (con confirmación)
- `tmux list-sessions` - Ver sesiones activas
- `tmux detach` - Desconectar sin matar

Si necesitas cerrar sesiones, pregunta primero: "¿Estás seguro de que quieres cerrar estas sesiones de tmux?"
