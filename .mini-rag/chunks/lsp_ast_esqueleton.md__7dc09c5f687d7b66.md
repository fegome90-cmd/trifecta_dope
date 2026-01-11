l "esqueleto". Se concatenan los tipos de nodo y sus identificadores (ej: Class:User, Method:login). Se genera un hash SHA-256 de esta cadena.
Beneficio: Si un desarrollador o el agente edita el cuerpo de una función (cambiando la lógica interna) pero no su firma, el hash del esqueleto estructural permanece idéntico. Esto indica al sistema que no es necesario invalidar ni actualizar el índice global de símbolos para referencias externas, ahorrando ciclos de cómputo valiosos en el bucle de retroalimentación.16
3. Inteligencia Semántica: Integración del Protocolo LSP
Mientras el AST proporciona la estructura sintáctica, el Protocolo de Servidor de Lenguaje (LSP) proporciona la inteligencia semántica: la capacidad de resolver tipos, encontrar definiciones a través de archivos y comprender la herencia. Sin embargo, los servidores LSP son tradicionalmente pesados y lentos en arrancar.
3.1 Arquitectura de Cliente Headless "Lean"
La implementación de un cliente LSP para un agente difiere radicalmente de la de un editor de texto. No hay interfaz gráfica, ni cursor humano, ni desplazamiento. El cliente debe ser Headless (sin cabeza) y actuar como un orquestador de procesos.17
Componentes del Cliente Headless:
Gestor de Ciclo de Vida (Lifecycle Manager): Responsable de iniciar el proceso del servidor (e.g., pyright-langserver, rust-analyzer), gestionar la comunicación mediante JSON-RPC s
