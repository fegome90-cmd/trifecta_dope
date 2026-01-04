#!/bin/bash
# Pre-commit hook: muestra instrucciones para actualizar sesión y sincronizar
# NO ejecuta nada automáticamente - solo muestra el prompt para el agente

cat << 'EOF'

╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️  ANTES DE COMMITEAR: Actualizar sesión + sincronizar contexto              ║
╚══════════════════════════════════════════════════════════════════════════════╝

1. AGREGAR entrada a _ctx/session_trifecta_dope.md (append):
   ```md
   ## YYYY-MM-DD HH:MM - <descripción>
   - Segment: .
   - Objective: <que necesitas resolver>
   - Plan: ctx sync -> ctx search -> ctx get
   - Commands: (pending/executed)
   - Evidence: (pending/[chunk_id] list)
   - Warnings: (none/<code>)
   - Next: <1 concrete step>
   ```

2. LUEGO ejecutar: uv run trifecta ctx sync -s .

EOF

exit 0
