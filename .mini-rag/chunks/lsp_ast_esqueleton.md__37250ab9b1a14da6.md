entación:
Extracción: Usar Tree-sitter para identificar todas las definiciones y llamadas a funciones en el proyecto.
Grafo de Referencias: Construir un grafo dirigido donde los nodos son archivos o símbolos y las aristas son las referencias (llamadas/importaciones).12
Ranking de Importancia: Aplicar el algoritmo PageRank sobre este grafo. Esto identifica matemáticamente los módulos más "centrales" o acoplados del sistema, que son estadísticamente los más relevantes para entender la arquitectura global.
Optimización de Contexto: Seleccionar los símbolos con mayor ranking hasta llenar el presupuesto de tokens (e.g., 1024 tokens), generando un mapa comprimido que se inyecta en el contexto del LLM.
Este enfoque proporciona una "visión periférica" superior a la búsqueda vectorial, ya que se basa en la estructura real de dependencias del código, no en la similitud de palabras.12
4.2 Selectores Semánticos y Estabilidad de Referencias (Caso Lanser-CLI)
Un problema crítico en agentes es la Deriva de Código (Code Drift). Un agente decide editar la línea 50, pero una edición previa insertó 5 líneas arriba, moviendo el objetivo a la línea 55. Las referencias archivo:línea:columna son frágiles y causan errores de aplicación de parches constantes.
La solución propuesta por Lanser-CLI es el uso de un Selector DSL (Domain Specific Language) semántico.4
Concepto: En lugar de referenciar coorde
