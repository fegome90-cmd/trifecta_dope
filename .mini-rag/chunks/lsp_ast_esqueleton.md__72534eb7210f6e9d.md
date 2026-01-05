gserver, rust-analyzer), gestionar la comunicación mediante JSON-RPC sobre stdio y asegurar un cierre limpio. Herramientas como Multilspy (Python) demuestran patrones robustos para abstraer la complejidad de descargar y configurar binarios de servidores específicos por lenguaje y sistema operativo.19
Proxy de Solicitudes: Convierte las intenciones del agente ("necesito ver la definición de foo") en mensajes JSON-RPC estandarizados (textDocument/definition).
Manejador de Eventos Asíncronos: Los servidores LSP pueden enviar notificaciones no solicitadas, como textDocument/publishDiagnostics (errores de compilación). El cliente debe capturar estos eventos y convertirlos en feedback accionable para el agente, en lugar de descartarlos.21
3.2 El Problema del "Virtual Document" y el Shadow Workspace
Uno de los hallazgos más críticos de esta investigación es la gestión de archivos no guardados. Un agente a menudo necesita "probar" un cambio o analizar código generado que aún no debe persistirse en el disco para evitar corromper el repositorio.
La especificación LSP permite la manipulación de Documentos Virtuales a través de las notificaciones de sincronización: textDocument/didOpen, textDocument/didChange, y textDocument/didClose.3
Patrón de Implementación "Shadow Workspace":
El agente propone una edición.
El cliente LSP no escribe en el disco. En su lugar, envía un textDocument/didCha
