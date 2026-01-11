LSP no escribe en el disco. En su lugar, envía un textDocument/didChange al servidor con el nuevo contenido, manteniendo la versión del archivo en un "Overlay" en memoria.3
El servidor LSP procesa este cambio en su modelo interno y recalcula los diagnósticos.
El cliente consulta los diagnósticos. Si hay errores graves, el agente recibe feedback negativo inmediato ("Tu código rompe la compilación") sin haber tocado el sistema de archivos real.
Solo si la validación pasa, se escribe el cambio en disco.
Este mecanismo es esencial para la seguridad y la "reversibilidad" (rollback) de las acciones del agente, actuando como un sandbox semántico.4
3.3 Set Mínimo de Requests para ROI Inmediato
Evitando la sobre-ingeniería de implementar todo el protocolo LSP (que incluye resaltado sintáctico, plegado de código, etc., irrelevantes para un agente), se identifica el siguiente set mínimo de capacidades para un ROI máximo 23:
Request LSP
Función para el Agente
Valor (ROI)
textDocument/definition
Navegación
Permite saltar de un uso a la implementación. Esencial para entender librerías desconocidas.
textDocument/references
Análisis de Impacto
"¿Quién llama a esta función?" Permite evaluar el riesgo de un cambio (side-effects).
textDocument/hover
Documentación
Recupera docstrings y firmas de tipos sin necesidad de leer/parsear el archivo de definición. Contexto barato.
textDocument/publishDia
